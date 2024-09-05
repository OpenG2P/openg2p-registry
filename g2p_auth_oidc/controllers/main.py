import logging

from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import OAuthLogin

_logger = logging.getLogger(__name__)


class OpenIDLogin(OAuthLogin):
    def list_providers(self, **kw):
        return request.env["auth.oauth.provider"].sudo().list_providers(**kw)
