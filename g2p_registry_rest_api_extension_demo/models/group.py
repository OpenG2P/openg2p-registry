from odoo.addons.g2p_registry_rest_api.models.group import GroupInfoOut


class GroupInfoOutExtended(GroupInfoOut, extends=GroupInfoOut):
    active: bool
