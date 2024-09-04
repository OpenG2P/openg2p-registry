import logging

import requests
import werkzeug.http
from jose import jwt

from odoo import api, fields, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    oidc_groups_reset = fields.Boolean(default=False)
    oidc_userinfo_reset = fields.Boolean(default=False)

    @api.model
    def auth_oauth(self, provider, params):
        try:
            oauth_provider = self.env["auth.oauth.provider"].browse(provider)

            if not oauth_provider.flow.startswith("oidc"):
                return super().auth_oauth(provider, params)

            oauth_provider.oidc_get_tokens(params)
            validation = oauth_provider.oidc_get_validation_dict(params)

            login = self._auth_oauth_signin(provider, validation, params)
            if not login:
                raise AccessDenied()
            return (self.env.cr.dbname, login, params["access_token"])
        except Exception as e:
            _logger.exception("auth_oauth exception")
            raise e

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        oauth_uid = validation["user_id"]
        try:
            oauth_user = self.search([("oauth_uid", "=", oauth_uid), ("oauth_provider_id", "=", provider)])
            if not oauth_user:
                raise AccessDenied()
            assert len(oauth_user) == 1
            oauth_provider.oidc_signin_update_userinfo(
                validation, params, oauth_partner=oauth_user.partner_id, oauth_user=oauth_user
            )
            oauth_provider.oidc_signin_update_groups(
                validation, params, oauth_partner=oauth_user.partner_id, oauth_user=oauth_user
            )
            oauth_user.write({"oauth_access_token": params["access_token"]})
            return oauth_user.login
        except AccessDenied as access_denied_exception:
            if self.env.context.get("no_user_creation"):
                return None
            return oauth_provider.oidc_signin_create_user(
                validation, params, access_denied_exception=access_denied_exception
            )

    def _auth_oauth_rpc(self, endpoint, access_token):
        # This method is recreated to suit that application/jwt response type
        if self.env["ir.config_parameter"].sudo().get_param("auth_oauth.authorization_header"):
            response = requests.get(
                endpoint,
                headers={"Authorization": "Bearer %s" % access_token},
                timeout=10,
            )
        else:
            response = requests.get(endpoint, params={"access_token": access_token}, timeout=10)

        if response.ok:  # nb: could be a successful failure
            if response.headers.get("content-type"):
                if "application/jwt" in response.headers["content-type"]:
                    # TODO: Improve the following
                    return jwt.get_unverified_claims(response.text)
                if "application/json" in response.headers["content-type"]:
                    return response.json()
        _logger.debug("Validation Response", response.text)
        auth_challenge = werkzeug.http.parse_www_authenticate_header(response.headers.get("WWW-Authenticate"))
        if auth_challenge.type == "bearer" and "error" in auth_challenge:
            return dict(auth_challenge)

        return {"error": "invalid_request"}
