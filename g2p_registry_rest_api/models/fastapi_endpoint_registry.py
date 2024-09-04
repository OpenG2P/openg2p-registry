from fastapi import APIRouter, FastAPI

from odoo import api, fields, models

from odoo.addons.fastapi.dependencies import (
    authenticated_partner_from_basic_auth_user,
    authenticated_partner_impl,
)


class G2PRegistryEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("registry", "Registry Endpoint")], ondelete={"registry": "cascade"}
    )

    def _get_fastapi_routers(self) -> list[APIRouter]:
        routers = super()._get_fastapi_routers()
        if self.app == "registry":
            # Cannot import these on top because of issues with dependency graph
            from ..routers.group import group_router
            from ..routers.individual import individual_router

            routers.extend([group_router, individual_router])
        return routers

    def _get_app(self) -> FastAPI:
        app = super()._get_app()
        if self.app == "registry":
            # For now limiting the authentication to Basic auth
            app.dependency_overrides[authenticated_partner_impl] = authenticated_partner_from_basic_auth_user
        return app

    @api.model
    def sync_endpoint_id_with_registry(self, endpoint_id):
        return self.browse(endpoint_id).action_sync_registry()
