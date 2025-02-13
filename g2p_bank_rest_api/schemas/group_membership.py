from odoo.addons.g2p_registry_rest_api.schemas import group_membership

from . import bank_details


class GroupMembersInfoRequest(
    group_membership.GroupMembersInfoRequest, extends=group_membership.GroupMembersInfoRequest
):
    bank_ids: list[bank_details.BankDetailsRequest] | None = None
