from werkzeug.utils import redirect as werkzeug_redirect

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.session import Session


class OAuthLogoutController(Session):
    @http.route("/web/session/logout", type="http", auth="user")
    def logout(self, redirect="/web"):
        user = request.env.user
        provider = user.oauth_provider_id

        # Redirect to OAuth provider logout URL if configured
        if provider and provider.logout_uri:
            request.session.logout()
            redirect = provider.logout_uri
            return werkzeug_redirect(redirect, 302)

        return super().logout(redirect=redirect)
