import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import authenticated_partner_env

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from ..schemas.group import GroupInfoRequest, GroupInfoResponse, GroupShortInfoOut

_logger = logging.getLogger(__name__)

group_router = APIRouter(tags=["group"])


@group_router.get("/group/{_id}", responses={200: {"model": GroupInfoResponse}})
def get_group(_id, env: Annotated[Environment, Depends(authenticated_partner_env)]):
    """
    Get partner's information by ID
    """
    partner = _get_group(env, _id)

    if partner:
        return GroupInfoResponse.model_validate(partner)
    else:
        raise G2PApiValidationError(
            error_message=G2PErrorCodes.G2P_REQ_010.get_error_message(),
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
            error_description=("Record is not present in the database."),
        )


@group_router.get(
    "/group",
    responses={200: {"model": list[GroupInfoResponse]}},
)
def search_groups(
    env: Annotated[Environment, Depends(authenticated_partner_env)],
    _id: int | None = None,
    name: str | None = None,
    include_members_full: bool = False,
):
    """
    Search for groups by ID or name
    """
    domain = [("is_registrant", "=", True), ("is_group", "=", True)]
    error_description = ""

    if _id:
        domain.append(("id", "=", _id))
        error_description = "This ID does not exist. Please enter a valid ID."

    if name:
        domain.append(("name", "like", name))
        error_description = "This Name does not exist. Please enter a valid Name."

    res = []

    for p in env["res.partner"].sudo().search(domain):
        if include_members_full:
            res.append(GroupInfoResponse.model_validate(p))
        else:
            res.append(GroupShortInfoOut.model_validate(p))
    if not len(res):
        if name and _id:
            error_description = "Entered Name and ID does not exist."
        raise G2PApiValidationError(
            error_message=G2PErrorCodes.G2P_REQ_010.get_error_message(),
            error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
            error_description=error_description,
        )
    return res


@group_router.post("/group", responses={200: {"model": GroupInfoResponse}})
def create_group(request: GroupInfoRequest, env: Annotated[Environment, Depends(authenticated_partner_env)]):
    """
    Create a new Group
    """
    # Create the individual Objects
    grp_membership_rec = []

    for membership_info in request.members:
        individual = membership_info

        indv_rec = env["process_individual.rest.mixin"]._process_individual(individual)

        _logger.info("Creating Individual Record")
        indv_id = env["res.partner"].sudo().create(indv_rec)

        # Add individual's membership kind fields
        membership_kind = membership_info.kind

        indv_membership_kinds = []
        if membership_kind:
            for kind in membership_kind:
                # Search Kind
                kind_id = env["g2p.group.membership.kind"].sudo().search([("name", "=", kind.name)])
                if kind_id:
                    indv_membership_kinds.append((4, kind_id[0].id))
                elif kind.name:
                    raise G2PApiValidationError(
                        error_message=G2PErrorCodes.G2P_REQ_004.get_error_message(),
                        error_code=G2PErrorCodes.G2P_REQ_004.get_error_code(),
                        error_description="Membership kind - %s is not present in the database." % kind.name,
                    )
        grp_membership_rec.append({"individual": indv_id.id, "kind": indv_membership_kinds})

    # create the group object
    grp_rec = env["process_group.rest.mixin"]._process_group(request)

    _logger.info("Creating Group Record")
    grp_id = env["res.partner"].sudo().create(grp_rec)
    for mbr in grp_membership_rec:
        mbr_rec = mbr
        mbr_rec.update({"group": grp_id.id})

        env["g2p.group.membership"].sudo().create(mbr_rec)

    # Reload the new object from the DB
    partner = _get_group(env, grp_id.id)

    return GroupInfoResponse.model_validate(partner)


def _get_group(env: Environment, _id: int):
    return (
        env["res.partner"]
        .sudo()
        .search([("id", "=", _id), ("is_registrant", "=", True), ("is_group", "=", True)])
    )
