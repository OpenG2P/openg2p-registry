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
async def get_individual(
    _id,
    env: Annotated[Environment, Depends(authenticated_partner_env)],
):
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
    request: IndividualInfoRequest,
    env: Annotated[Environment, Depends(authenticated_partner_env)],
) -> IndividualInfoResponse:
    """
    Create a new individual
    """
    indv_rec = env["process_individual.rest.mixin"]._process_individual(request)
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
    Get registration IDs for individuals that:
    - are registrants
    - are not groups
    - are active
    - have at least one valid ID of `include_id_type`
    - do NOT have any ID of `exclude_id_type` (if provided)
    """
    if not include_id_type:
        raise G2PApiValidationError(
            error_message="Record is not present in the database.",
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        )

    try:
        # Resolve include / exclude id types by name on g2p.id.type
        id_type_model = env["g2p.id.type"].sudo()

        include_type_rec = id_type_model.search([("name", "=", include_id_type)], limit=1)
        if not include_type_rec:
            raise G2PApiValidationError(
                error_message=f"Unknown include_id_type: {include_id_type}",
                error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
            )

        exclude_type_rec = None
        if exclude_id_type:
            exclude_type_rec = id_type_model.search([("name", "=", exclude_id_type)], limit=1)

        reg_id_model = env["g2p.reg.id"].sudo()

        # Get all valid reg_ids of the include type, with partner constraints
        include_reg_ids = reg_id_model.search(
            [
                ("id_type", "=", include_type_rec.id),
                ("status", "=", "valid"),
                ("partner_id.is_registrant", "=", True),
                ("partner_id.is_group", "=", False),
                ("partner_id.active", "=", True),
            ]
        )

        result_ids: set[str] = set()

        for reg in include_reg_ids:
            partner = reg.partner_id
            if not partner:
                continue

            # If exclude type provided, skip partners that have any reg_id of that type
            if exclude_type_rec:
                has_exclude = bool(
                    partner.reg_ids.filtered(
                        lambda x, exclude_type_id=exclude_type_rec.id: x.id_type.id == exclude_type_id
                    )
                )
                if has_exclude:
                    continue

            result_ids.add(reg.value)

        return list(result_ids)

    except G2PApiValidationError:
        # Bubble up explicit API errors
        raise
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
    results: list[UpdateIndividualInfoResponse] = []

    if not id_type:
        raise G2PApiValidationError(
            error_message="ID type is required for update individual",
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        )

    try:
        id_type_rec = env["g2p.id.type"].sudo().search([("name", "=", id_type)], limit=1)
    except Exception as e:
        _logger.exception("Error resolving g2p.id.type")
        raise G2PApiValidationError(
            error_message=str(e),
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        ) from e

    if not id_type_rec:
        raise G2PApiValidationError(
            error_message=f"Unknown ID type: {id_type}",
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        )

    reg_id_model = env["g2p.reg.id"].sudo()

    for request in requests:
        try:
            _id = request.updateId

            if not _id:
                raise G2PApiValidationError(
                    error_message="updateId is required for update individual",
                    error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
                )

            # Exact reg_id row match for (value, id_type)
            reg_id = reg_id_model.search(
                [
                    ("value", "=", _id),
                    ("id_type", "=", id_type_rec.id),
                ],
                limit=1,
            )

            if not reg_id:
                raise G2PApiValidationError(
                    error_message=(
                        f"Individual with the given ID '{_id}' and " f"type '{id_type}' not found."
                    ),
                    error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
                )

            partner_rec = reg_id.partner_id

            if not partner_rec or not partner_rec.active:
                raise G2PApiValidationError(
                    error_message=(f"Individual with the given ID '{_id}' not found or not active."),
                    error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
                )

            indv_rec = env["process_individual.rest.mixin"]._process_individual(request)

            reg_ids_cmds = indv_rec.get("reg_ids", []) or []
            for i, reg_cmd in enumerate(reg_ids_cmds):
                vals = reg_cmd[2] if len(reg_cmd) > 2 else {}
                id_type_id = vals.get("id_type")

                if not id_type_id:
                    continue

                id_rec_existing = partner_rec.reg_ids.filtered(
                    lambda x, id_type_id=id_type_id: x.id_type.id == id_type_id
                )

                if id_rec_existing:
                    reg_ids_cmds[i] = (1, id_rec_existing.id, vals)

            if reg_ids_cmds:
                indv_rec["reg_ids"] = reg_ids_cmds

            partner_rec.write(indv_rec)
            results.append(UpdateIndividualInfoResponse.model_validate(partner_rec))

        except G2PApiValidationError:
            raise
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
