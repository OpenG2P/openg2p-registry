from odoo import http
from odoo.tools.translate import _

from odoo.addons.web.controllers.home import Home


class WebLoginHome(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        response = super().web_login()
        if "error" in response.qcontext:
            error_message = response.qcontext["error"]
            if error_message == _("Wrong login/password"):
                # Change the error message to your desired message
                response.qcontext["error"] = _("Login failed due to Invalid credentials !")
        return response
