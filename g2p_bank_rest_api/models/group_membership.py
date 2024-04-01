from odoo.addons.g2p_registry_rest_api.models import group_membership

from . import bank_details


class GroupMembersInfoIn(group_membership.GroupMembersInfoIn, extends=group_membership.GroupMembersInfoIn):
    bank_ids: list[bank_details.BankDetailsIn] | None
