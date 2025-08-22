from fastapi import APIRouter

from odoo import api, fields, models

from ..routers.registry_search import g2p_connect_router


class G2PConnectFastApiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("g2p_connect_registry", "G2P Connect Registry Endpoint")],
        ondelete={"g2p_connect_registry": "cascade"},
    )

    def _get_fastapi_routers(self) -> list[APIRouter]:
        routers = super()._get_fastapi_routers()
        if self.app == "g2p_connect_registry":
            routers.append(g2p_connect_router)
        return routers

    @api.model
    def sync_endpoint_id_with_registry(self, endpoint_id):
        return self.browse(endpoint_id).action_sync_registry()
