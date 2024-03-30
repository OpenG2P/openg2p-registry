from typing import Union

from odoo.addons.g2p_registry_rest_api.models import group_membership


class GroupMembersInfoIn(group_membership.GroupMembersInfoIn, extends=group_membership.GroupMembersInfoIn):
    additional_g2p_info: Union[list[dict], dict] = None
