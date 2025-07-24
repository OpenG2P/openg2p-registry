import logging

from odoo.http import request

from odoo.addons.g2p_auth_oidc.controllers.main import OpenIDLogin
from odoo.addons.web.controllers.utils import ensure_db

_logger = logging.getLogger(__name__)


class DisableLoginController(OpenIDLogin):
    def web_login(self, *args, **kw):
        ensure_db()
        if not request.params.get("oauth_error"):
            provider_id = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("g2p_disable_password_login.direct_oauth_provider", default=None)
                or None
            )
            if provider_id:
                provider_dict = (
                    request.env["auth.oauth.provider"]
                    .sudo()
                    .list_providers(
                        domain=[("id", "=", int(provider_id)), ("enabled", "=", True)],
                        redirect=kw.get("redirect") or None,
                        **kw,
                    )
                )
                if provider_dict:
                    provider_dict = provider_dict[0]
                    return request.redirect(provider_dict["auth_link"], code=302, local=False)
        return super().web_login(*args, **kw)
