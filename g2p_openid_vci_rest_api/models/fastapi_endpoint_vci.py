from fastapi import APIRouter

from odoo import api, fields, models

from ..routers.openid_vci import openid_vci_router


class VCIFastApiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(selection_add=[("vci", "VCI Endpoint")], ondelete={"vci": "cascade"})

    def _get_fastapi_routers(self) -> list[APIRouter]:
        routers = super()._get_fastapi_routers()
        if self.app == "vci":
            routers.append(openid_vci_router)
        return routers

    @api.model
    def sync_endpoint_id_with_registry(self, endpoint_id):
        return self.browse(endpoint_id).action_sync_registry()
