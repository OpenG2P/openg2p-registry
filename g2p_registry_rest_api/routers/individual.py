import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from ..schemas.individual import IndividualInfoRequest, IndividualInfoResponse

individual_router = APIRouter(prefix="/individual", tags=["individual"])


@individual_router.get("/{_id}", responses={200: {"model": IndividualInfoResponse}})
async def get_individual(_id, env: Annotated[Environment, Depends(odoo_env)]):
    """
    Get partner's information by ID
    """
    partner = _get_individual(env, _id)
    if partner:
        return IndividualInfoResponse.model_validate(partner)
    else:
        _handle_error(G2PErrorCodes.G2P_REQ_010, "Record is not present in the database.")


@individual_router.get(
    "",
    responses={200: {"model": list[IndividualInfoResponse]}},
)
def search_individuals(
    env: Annotated[Environment, Depends(odoo_env)],
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
        _handle_error(G2PErrorCodes.G2P_REQ_010, error_message)

    return [IndividualInfoResponse.model_validate(partner) for partner in partners]


@individual_router.post(
    "/",
    responses={200: {"model": IndividualInfoResponse}},
)
def create_individual(
    request: IndividualInfoRequest, env: Annotated[Environment, Depends(odoo_env)]
) -> IndividualInfoResponse:
    """
    Create a new individual
    """
    # Create the individual Object
    indv_rec = env["process_individual.rest.mixin"]._process_individual(request)

    logging.info("Individual Api: Creating Individual Record")
    indv_id = env["res.partner"].sudo().create(indv_rec)

    partner = _get_individual(env, indv_id.id)

    return IndividualInfoResponse.model_validate(partner)


def _get_individual(env: Environment, _id: int):
    return (
        env["res.partner"]
        .sudo()
        .search([("id", "=", _id), ("is_registrant", "=", True), ("is_group", "=", False)])
    )


def _handle_error(error_code, error_description):
    raise G2PApiValidationError(
        error_message=error_code.get_error_message(),
        error_code=error_code.get_error_code(),
        error_description=error_description,
    )
