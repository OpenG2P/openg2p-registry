from fastapi import APIRouter

from odoo import api, fields, models

from ..routers.group import group_router
from ..routers.individual import individual_router


class G2PRegistryEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("registry", "Registry Endpoint")], ondelete={"registry": "cascade"}
    )

    def _get_fastapi_routers(self) -> list[APIRouter]:
        routers = super()._get_fastapi_routers()
        if self.app == "registry":
            routers.append(group_router)
            routers.append(individual_router)
        return routers

    @api.model
    def sync_endpoint_id_with_registry(self, endpoint_id):
        return self.browse(endpoint_id).action_sync_registry()
