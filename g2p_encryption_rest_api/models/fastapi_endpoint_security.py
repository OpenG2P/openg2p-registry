from fastapi import APIRouter

from odoo import api, fields, models

from ..routers.well_known import well_known_router


class SecurityFastApiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("security", "Security Endpoint")], ondelete={"security": "cascade"}
    )

    def _get_fastapi_routers(self) -> list[APIRouter]:
        routers = super()._get_fastapi_routers()
        if self.app == "security":
            routers.append(well_known_router)
        return routers

    @api.model
    def sync_endpoint_id_with_registry(self, endpoint_id):
        return self.browse(endpoint_id).action_sync_registry()
