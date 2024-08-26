import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import authenticated_partner_env

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from ..schemas.individual import (
    IndividualInfoRequest,
    IndividualInfoResponse,
    UpdateIndividualInfoRequest,
    UpdateIndividualInfoResponse,
)

_logger = logging.getLogger(__name__)

individual_router = APIRouter(tags=["individual"])


@individual_router.get("/individual/{_id}", responses={200: {"model": IndividualInfoResponse}})
async def get_individual(_id, env: Annotated[Environment, Depends(authenticated_partner_env)]):
    """
    Get partner's information by ID
    """
    partner = _get_individual(env, _id)
    if partner:
        return IndividualInfoResponse.model_validate(partner)
    else:
        raise G2PApiValidationError(
            error_message="Record is not present in the database.",
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        )


@individual_router.get(
    "/individual",
    responses={200: {"model": list[IndividualInfoResponse]}},
)
def search_individuals(
    env: Annotated[Environment, Depends(authenticated_partner_env)],
    _id: int | None = None,
    name: str | None = None,
) -> list[IndividualInfoResponse]:
    """
    Search for individuals by ID or name
    """

    domain = [("is_registrant", "=", True), ("is_group", "=", False)]

    if _id:
        domain.append(("id", "=", _id))
    if name:
        domain.append(("name", "like", name))

    partners = env["res.partner"].sudo().search(domain)
    if not partners:
        error_message = "The specified criteria did not match any records."
        raise G2PApiValidationError(
            error_message=error_message,
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        )

    return [IndividualInfoResponse.model_validate(partner) for partner in partners]


@individual_router.post(
    "/individual",
    responses={200: {"model": IndividualInfoResponse}},
)
def create_individual(
    request: IndividualInfoRequest, env: Annotated[Environment, Depends(authenticated_partner_env)]
) -> IndividualInfoResponse:
    """
    Create a new individual
    """
    # Create the individual Object
    indv_rec = env["process_individual.rest.mixin"]._process_individual(request)

    _logger.info("Individual Api: Creating Individual Record")
    indv_id = env["res.partner"].sudo().create(indv_rec)

    partner = _get_individual(env, indv_id.id)

    return IndividualInfoResponse.model_validate(partner)


@individual_router.get(
    "/get_individual_ids",
    responses={200: {"model": list[str]}},
)
async def get_individual_ids(
    env: Annotated[Environment, Depends(authenticated_partner_env)],
    include_id_type: str | None = "",
    exclude_id_type: str | None = "",
):
    """
    Get the IDs of an individual
    """

    if not include_id_type:
        raise G2PApiValidationError(
            error_message="Record is not present in the database.",
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        )
    try:
        domain = [("is_registrant", "=", True), ("is_group", "=", False), ("active", "=", True)]
        if include_id_type:
            domain.extend([("reg_ids.id_type", "=", include_id_type), ("reg_ids.status", "=", "valid")])

        registrant_rec = env["res.partner"].sudo().search(domain)

        all_ids = set()

        for partner in registrant_rec:
            has_exclude_id_type = any(reg_id.id_type.name == exclude_id_type for reg_id in partner.reg_ids)
            if has_exclude_id_type:
                continue
            for reg_id in partner.reg_ids:
                if reg_id.id_type.name == include_id_type:
                    all_ids.add(reg_id.value)

        return list(all_ids)

    except Exception as e:
        _logger.exception("Error while getting IDs")
        raise G2PApiValidationError(
            error_message="An error occurred while getting IDs.",
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        ) from e


@individual_router.put("/update_individual", responses={200: {"model": UpdateIndividualInfoResponse}})
async def update_individual(
    requests: list[UpdateIndividualInfoRequest],
    env: Annotated[Environment, Depends(authenticated_partner_env)],
    id_type: str | None = "",
) -> list[UpdateIndividualInfoResponse]:
    """
    Update an individual
    """
    results = []

    for request in requests:
        try:
            _logger.debug(f"Request data: {request}")
            _id = request.updateId
            if _id and id_type:
                partner_rec = (
                    env["res.partner"]
                    .sudo()
                    .search(
                        [
                            ("reg_ids.value", "=", _id),
                            ("reg_ids.id_type", "=", id_type),
                            ("active", "=", True),
                        ],
                        limit=1,
                    )
                )
                if not partner_rec:
                    raise G2PApiValidationError(
                        error_message=f"Individual with the given ID {_id} not found.",
                        error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
                    )

                # Update the individual
                indv_rec = env["process_individual.rest.mixin"]._process_individual(request)

                for reg_id in indv_rec["reg_ids"]:
                    id_type_id = reg_id[2].get("id_type")
                    value = reg_id[2].get("value")

                    id_rec = (
                        env["g2p.reg.id"]
                        .sudo()
                        .search(
                            [
                                ("value", "=", value),
                                ("id_type", "=", id_type_id),
                            ],
                            limit=1,
                        )
                    )
                    if id_rec:
                        id_rec.unlink()

                partner_rec.write(indv_rec)
                results.append(UpdateIndividualInfoResponse.model_validate(partner_rec))
            else:
                _logger.error("ID & ID type is required for update individual")
                raise G2PApiValidationError(
                    error_message="ID is required for update individual",
                    error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
                )

        except Exception as e:
            _logger.exception("Error occurred while updating the partner with ID")
            raise G2PApiValidationError(
                error_message=str(e),
                error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
            ) from e

    return results


def _get_individual(env: Environment, _id: int):
    return (
        env["res.partner"]
        .sudo()
        .search([("id", "=", _id), ("is_registrant", "=", True), ("is_group", "=", False)])
    )
