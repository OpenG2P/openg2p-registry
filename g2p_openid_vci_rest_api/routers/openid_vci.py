import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

from ..schemas.openid_vci import (
    CredentialBaseResponse,
    CredentialErrorResponse,
    CredentialIssuerResponse,
    CredentialRequest,
    CredentialResponse,
    VCIBaseModel,
)

_logger = logging.getLogger(__name__)

openid_vci_router = APIRouter(tags=["openid vci"])


@openid_vci_router.post("/credential", responses={200: {"model": CredentialBaseResponse}})
def post_credential(
    credential_request: CredentialRequest,
    env: Annotated[Environment, Depends(odoo_env)],
    authorization: Annotated[str, Header()] = "",
):
    token = authorization.removeprefix("Bearer")
    if not token:
        raise HTTPException(401, "Invalid Bearer Token received.")
    try:
        # TODO: Split into smaller steps to better handle errors
        return CredentialResponse(
            **env["g2p.openid.vci.issuers"].issue_vc(credential_request.model_dump(), token.strip())
        )
    except Exception as e:
        _logger.exception("Error while handling credential request")
        # TODO: Remove this hardcoding
        return CredentialErrorResponse(
            error="invalid_credential_request",
            error_description=f"Error issuing credential. {e}",
            c_nonce="",
            c_nonce_expires_in=1,
        )


@openid_vci_router.get(
    "/.well-known/openid-credential-issuer/{issuer_name}",
    responses={200: {"model": CredentialIssuerResponse}},
)
def get_openid_credential_issuer(
    issuer_name: str | None,
    env: Annotated[Environment, Depends(odoo_env)],
):
    return CredentialIssuerResponse(
        **env["g2p.openid.vci.issuers"].get_issuer_metadata_by_name(issuer_name=issuer_name)
    )


@openid_vci_router.get(
    "/.well-known/openid-credential-issuer", responses={200: {"model": CredentialIssuerResponse}}
)
def get_openid_credential_issuers_all(
    env: Annotated[Environment, Depends(odoo_env)],
):
    return get_openid_credential_issuer(issuer_name=None, env=env)


@openid_vci_router.get("/.well-known/contexts.json", responses={200: {"model": VCIBaseModel}})
def get_openid_contexts_json(
    env: Annotated[Environment, Depends(odoo_env)],
):
    return VCIBaseModel(**env["g2p.openid.vci.issuers"].get_all_contexts_json())
