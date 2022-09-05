from odoo.addons.g2p_registry_rest_api.models.group import GroupInfoOut


class GroupInfoOutExtended(GroupInfoOut, extends=GroupInfoOut):
    z_ind_grp_num_children: int
