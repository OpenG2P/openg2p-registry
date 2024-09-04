import json
import logging
import traceback

from werkzeug.exceptions import BadRequest

from odoo import http
from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import fragment_to_query_string
from odoo.addons.web.controllers.utils import ensure_db

_logger = logging.getLogger(__name__)


class RegIdOidcController(http.Controller):
    @http.route("/auth_oauth/g2p_registry_id/authenticate", type="http", auth="user")
    @fragment_to_query_string
    def g2p_reg_id_authenticate(self, **kw):
        state = json.loads(kw["state"])
        dbname = state["d"]
        if not http.db_filter([dbname]):
            return BadRequest("DB cannot be empty")
        ensure_db(db=dbname)

        provider = state["p"]
        reg_id_id = state["reg_id"]
        response_values = {
            "authentication_status": False,
            "error_exception": None,
        }
        try:
            oauth_provider = request.env["auth.oauth.provider"].sudo().browse(provider)
            reg_id = request.env["g2p.reg.id"].browse(reg_id_id)

            if not oauth_provider.flow.startswith("oidc"):
                # TODO: Support Oauth2 flow also.
                raise BadRequest("Oauth2 Provider not supported!")

            oauth_provider.oidc_get_tokens(kw)
            validation = oauth_provider.oidc_get_validation_dict(kw)
            oauth_provider.oidc_signin_generate_user_values(
                validation, kw, oauth_partner=reg_id.partner_id, oauth_user=None, create_user=False
            )
            if validation["user_id"] and reg_id.value == validation["user_id"]:
                reg_id.partner_id.update({"reg_ids": validation["reg_ids"]})
                response_values["authentication_status"] = True
                reg_id.last_authentication_user_id = request.env.user.id
                reg_id.description = None
                response_values["validation"] = validation
            else:
                reg_id.update(
                    {
                        "authentication_status": "not_authenticated",
                        "description": "ID value does not match",
                    }
                )
        except Exception:
            _logger.exception("Encountered error while authenticating Reg Id.")
            response_values["error_exception"] = traceback.format_exc()

        return request.render("g2p_auth_id_oidc.g2p_reg_id_authenticate", response_values)
