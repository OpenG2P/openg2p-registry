from odoo.addons.g2p_registry_rest_api.schemas.group_membership import GroupMembersInfoRequest


class GroupMembersInfoIn(GroupMembersInfoRequest, extends=GroupMembersInfoRequest):
    additional_g2p_info: dict | list | None = None
