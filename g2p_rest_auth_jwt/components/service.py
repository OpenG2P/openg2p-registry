# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from odoo.addons.component.core import AbstractComponent

from ..apispec.rest_method_security_plugin import RestMethodSecurityPlugin


class BaseRestService(AbstractComponent):
    _inherit = "base.rest.service"

    def _get_api_spec(self, **params):
        spec = super(BaseRestService, self)._get_api_spec(**params)
        plugin = RestMethodSecurityPlugin(self)
        plugin.init_spec(spec)
        spec.plugins.append(plugin)
        return spec
