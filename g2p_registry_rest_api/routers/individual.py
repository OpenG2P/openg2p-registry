import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from odoo.api import Environment
from odoo.osv import expression

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
    responses={200: {"model": list[str] | list[list[str | None]]}},
)
async def get_individual_ids(
    env: Annotated[Environment, Depends(authenticated_partner_env)],
    include_id_type: Annotated[list[str] | None, Query()] = None,
    exclude_id_type: str | None = "",
    fayda_processed: str | None = None,
) -> list[str] | list[list[str | None]]:
    """
    Get registration IDs for individuals that:
    - are registrants
    - are not groups
    - are active
    - have at least one valid ID of any requested `include_id_type`
    - do NOT have any ID of `exclude_id_type` (if provided)
    - optionally match the `fayda_processed` state on the registration ID row
    """
    include_id_types = _normalize_id_types(include_id_type)

    if not include_id_types:
        raise G2PApiValidationError(
            error_message="Record is not present in the database.",
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
        )

    try:
        # Resolve include / exclude id types by name on g2p.id.type
        id_type_model = env["g2p.id.type"].sudo()

        include_type_recs = id_type_model.search([("name", "in", include_id_types)])
        include_type_by_name = {rec.name: rec for rec in include_type_recs}
        missing_include_types = [
            include_type for include_type in include_id_types if include_type not in include_type_by_name
        ]
        if missing_include_types:
            raise G2PApiValidationError(
                error_message=f"Unknown include_id_type: {', '.join(missing_include_types)}",
                error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
            )

        exclude_type_rec = None
        if exclude_id_type:
            exclude_type_rec = id_type_model.search([("name", "=", exclude_id_type)], limit=1)

        reg_id_model = env["g2p.reg.id"].sudo()
        include_type_recs = [include_type_by_name[include_id_type] for include_id_type in include_id_types]
        include_type_ids = [include_type_rec.id for include_type_rec in include_type_recs]

        # Get all reg_ids of the include type, with partner constraints.
        include_domain = [
            ("id_type", "in", include_type_ids),
            ("partner_id.is_registrant", "=", True),
            ("partner_id.is_group", "=", False),
            ("partner_id.active", "=", True),
        ]
        fayda_processed_values = _normalize_fayda_processed_value(fayda_processed)
        if fayda_processed_values:
            include_domain = expression.AND(
                [
                    include_domain,
                    expression.OR([[("fayda_processed", "=", value)] for value in fayda_processed_values]),
                ]
            )

        include_reg_ids = reg_id_model.search(include_domain)

        if len(include_type_recs) > 1:
            return _get_multiple_individual_id_rows(include_reg_ids, include_type_recs, exclude_type_rec)

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


def _normalize_id_types(include_id_type: list[str] | str | None) -> list[str]:
    if isinstance(include_id_type, str):
        include_id_type = [include_id_type]

    result = []
    seen = set()
    for id_type in include_id_type or []:
        id_type = id_type.strip()
        if id_type and id_type not in seen:
            result.append(id_type)
            seen.add(id_type)
    return result


def _normalize_fayda_processed_value(fayda_processed: str | None) -> list[str | bool]:
    if fayda_processed is None:
        return []

    normalized_text = str(fayda_processed).strip().lower()

    if normalized_text == "true":
        return ["true"]

    if normalized_text == "false":
        return ["false", False, ""]

    raise G2PApiValidationError(
        error_message="Invalid fayda_processed value. Expected 'true' or 'false'.",
        error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
    )


def _get_multiple_individual_id_rows(
    include_reg_ids, include_type_recs, exclude_type_rec
) -> list[list[str | None]]:
    partner_values_by_id = {}
    partners_by_id = {}

    for reg in include_reg_ids:
        partner = reg.partner_id
        if not partner:
            continue

        partners_by_id[partner.id] = partner
        values_by_type = partner_values_by_id.setdefault(partner.id, {})
        values_by_type.setdefault(reg.id_type.id, reg.value)

    result_ids = []
    for partner_id, values_by_type in partner_values_by_id.items():
        partner = partners_by_id[partner_id]

        if exclude_type_rec:
            has_exclude = bool(
                partner.reg_ids.filtered(
                    lambda x, exclude_type_id=exclude_type_rec.id: x.id_type.id == exclude_type_id
                )
            )
            if has_exclude:
                continue

        row = [values_by_type.get(include_type_rec.id) for include_type_rec in include_type_recs]
        result_ids.append(row)

    return result_ids


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
                    error_message="ID is required for update individual",
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
                id_value = vals.get("value")

                if not id_type_id:
                    continue

                id_rec_existing = reg_id_model.search(
                    [
                        ("partner_id", "=", partner_rec.id),
                        ("id_type", "=", id_type_id),
                        ("value", "=", id_value),
                    ],
                    limit=1,
                )
                if not id_rec_existing:
                    id_rec_existing = reg_id_model.search(
                        [
                            ("partner_id", "=", partner_rec.id),
                            ("id_type", "=", id_type_id),
                        ],
                        limit=1,
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
