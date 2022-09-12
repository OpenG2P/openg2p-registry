import pydantic

from odoo.addons.g2p_registry_rest_api.models.group import GroupInfoOut


class GroupInfoOutExtended(GroupInfoOut, extends=GroupInfoOut):
    area: int = pydantic.Field(..., alias="area_id")
