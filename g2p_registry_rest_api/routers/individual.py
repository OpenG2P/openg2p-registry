import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from ..schemas.individual import IndividualInfoRequest, IndividualInfoResponse, UpdateIndividualInfoRequest

individual_router = APIRouter(tags=["individual"])


@individual_router.get("/individual/{_id}", responses={200: {"model": IndividualInfoResponse}})
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
    "/individual",
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
    "/individual/",
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


@individual_router.get(
    "/get_ids",
    responses={200: {"model": list[str]}},
)
async def get_ids(
    env: Annotated[Environment, Depends(odoo_env)],
    include_id_type: str | None = "",
    exclude_id_type: str | None = "",
):
    """
    Get the IDs of an individual
    """

    try:
        if not include_id_type:
            _handle_error(G2PErrorCodes.G2P_REQ_010, "Record is not present in the database.")

        domain = [("is_registrant", "=", True), ("is_group", "=", False)]
        if include_id_type:
            domain.append(("reg_ids.id_type", "=", include_id_type))

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
        logging.error(f"Error while getting IDs: {str(e)}")
        _handle_error(G2PErrorCodes.G2P_REQ_010, "An error occurred while getting IDs.")


@individual_router.put("/update_individual", responses={200: {"model": IndividualInfoResponse}})
async def update_individual(
    requests: list[UpdateIndividualInfoRequest],
    env: Annotated[Environment, Depends(odoo_env)],
    id_type: str | None = "",
) -> list[IndividualInfoResponse]:
    """
    Update an individual
    """
    results = []

    for request in requests:
        try:
            logging.info(f"!!!!!!!!Request data: {request}")
            _id = request.updateId
            if _id and id_type:
                partner_rec = (
                    env["res.partner"]
                    .sudo()
                    .search([("reg_ids.value", "=", _id), ("reg_ids.id_type", "=", id_type)], limit=1)
                )
                if not partner_rec:
                    _handle_error(
                        G2PErrorCodes.G2P_REQ_010,
                        f"Individual with the given ID {_id} not found.",
                    )

                # Update the individual
                indv_rec = env["process_individual.rest.mixin"]._process_individual(request)

                logging.info("Individual Api: Updating Individual Record", indv_rec)

                partner_rec.write(indv_rec)

                results.append(IndividualInfoResponse.model_validate(partner_rec))

            else:
                logging.error("ID & ID type is required for update individual")
                _handle_error(G2PErrorCodes.G2P_REQ_010, "ID is required for update individual")

        except Exception as e:
            logging.error(f"Error occurred while updating the partner with ID {str(e)}")
            results.append({"Id": request.updateId, "status": "Failure", "message": str(e)})

    return results


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
