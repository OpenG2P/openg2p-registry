import json
import logging
from datetime import datetime, timezone
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, Header, HTTPException
from jose import jwt

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env
from odoo.addons.graphql_base import GraphQLControllerMixin

from ..schemas.graphql_schema import schema
from ..schemas.header import HeaderResponse
from ..schemas.message import MessageResponse, SingleSearchResponse
from ..schemas.registry_search import RegistrySearchRequest, RegistrySearchResponse

_logger = logging.getLogger(__name__)

g2p_connect_router = APIRouter()

cache_jwks = {}


@g2p_connect_router.post(
    "/registry/sync/search",
    responses={200: {"model": RegistrySearchResponse}},
)
async def registry_search(
    search_request: RegistrySearchRequest,
    env: Annotated[Environment, Depends(odoo_env)],
    Authorization: Annotated[str, Header()] = "",
):
    token = Authorization.removeprefix("Bearer").strip()

    if not token:
        raise HTTPException(401, "Missing authorization header.")

    iss_uri = env["ir.config_parameter"].sudo().get_param("g2p_registry_g2p_connect_rest_api.auth_iss", "")

    jwks_uri = (
        env["ir.config_parameter"].sudo().get_param("g2p_registry_g2p_connect_rest_api.auth_jwks_uri", "")
    )

    verified, payload = verify_auth_token(token, iss_uri, jwks_uri)

    if not verified:
        raise HTTPException(status_code=401, detail="Invalid Access Token")

    message_id = search_request.header.message_id
    transaction_id = search_request.message.transaction_id
    search_requests = search_request.message.search_request

    today_isoformat = datetime.now(timezone.utc).isoformat()

    search_responses = []
    process_search_requests(search_requests, today_isoformat, search_responses)

    return RegistrySearchResponse(
        signature=search_request.signature,
        header=HeaderResponse(message_id=message_id, action="on-search", status="succ"),
        message=MessageResponse(
            transaction_id=transaction_id,
            search_response=[SingleSearchResponse.model_validate(res) for res in search_responses],
        ),
    )


def verify_auth_token(token, iss_uri, jwks_uri):
    try:
        if not cache_jwks:
            jwks_res = requests.get(jwks_uri, timeout=10)
            jwks_res.raise_for_status()
            cache_jwks.update(jwks_res.json())

        return True, jwt.decode(
            token,
            cache_jwks,
            options={
                "verify_aud": False,
                "verify_iss": False,
                "verify_sub": False,
            },
        )
    except Exception as e:
        return False, str(e)


def process_query(query_type, query, graphql_schema):
    if query_type == "graphql":
        _logger.debug("Graphql query:", query)
        response = GraphQLControllerMixin._process_request(
            None, graphql_schema, data={"query": query.strip()}
        )

        response_error = json.loads(response.data).get("errors", "")
        if response_error:
            _logger.error(response_error[0]["message"])
            raise HTTPException(404, response_error[0]["message"])

        return json.loads(response.data)["data"]

    else:
        raise NotImplementedError("Only graphql query type supported.")


def get_graphql_schema():
    # Override this method to import a different schema
    return schema.graphql_schema


def process_search_requests(search_requests, today_isoformat, search_responses):
    for req in search_requests:
        reference_id = req.reference_id
        search_criteria = req.search_criteria
        query_type = search_criteria.query_type
        reg_type = search_criteria.reg_type
        query = search_criteria.query

        schema = get_graphql_schema()

        query_result = process_query(query_type, query, schema)

        if query_result:
            search_responses.append(
                {
                    "reference_id": reference_id,
                    "timestamp": today_isoformat,
                    "status": "succ",
                    "data": {
                        "reg_type": reg_type,
                        "reg_records": query_result,
                    },
                }
            )

    return search_responses
