import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class G2PAuthOidcIdType(models.Model):
    _inherit = "g2p.id.type"

    auth_oauth_provider_id = fields.Many2one("auth.oauth.provider", required=False)


class G2PRegId(models.Model):
    _inherit = "g2p.reg.id"

    authentication_status = fields.Selection(
        [
            ("authenticated", "Authenticated"),
            ("not_authenticated", "Not authenticated"),
        ],
        default="not_authenticated",
    )
    last_authentication_time = fields.Datetime()
    last_authentication_user_id = fields.Many2one("res.users")
    auth_oauth_provider_id = fields.Many2one("auth.oauth.provider", related="id_type.auth_oauth_provider_id")

    @api.model
    def get_auth_oauth_provider(self, reg_id_id):
        reg_id = self.sudo().browse(reg_id_id)
        if reg_id.auth_oauth_provider_id:
            params = (
                self.env["auth.oauth.provider"]
                .sudo()
                .list_providers(
                    domain=[("id", "=", reg_id.auth_oauth_provider_id.id)],
                    oidc_redirect_uri="/auth_oauth/g2p_registry_id/authenticate",
                    reg_id=reg_id.id,
                )[0]
            )
            params["auth_link"] = params["auth_link"].replace("__value__", reg_id.value)
            return params
        return None
