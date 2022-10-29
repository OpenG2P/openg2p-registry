# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from odoo.http import request

from odoo.addons.component.core import AbstractComponent, Component


class AbstractAuthJwtAuthenticatedPartnerProvider(AbstractComponent):
    _name = "abstract.auth.jwt.authenticated.partner.provider"

    def _get_authenticated_partner_id(self):
        return request.jwt_partner_id


class BaseRestAuthJwtComponentContextProvider(Component):
    _name = "base.rest.auth.jwt.component.context.provider"
    _inherit = [
        "abstract.auth.jwt.authenticated.partner.provider",
        "base.rest.service.context.provider",
    ]
    _usage = "auth_jwt_component_context_provider"
