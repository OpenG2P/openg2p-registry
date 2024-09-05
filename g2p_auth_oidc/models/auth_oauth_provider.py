import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen

import requests
from jose import jwt
from werkzeug.urls import url_encode, url_quote_plus

from odoo import api, fields, models, tools
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request

from odoo.addons.auth_signup.models.res_users import SignupError

_logger = logging.getLogger(__name__)


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    flow = fields.Selection(
        [
            ("oauth2", "OAuth2"),
            ("oidc_implicit", "OpenID Connect Implicit flow"),
            ("oidc_auth_code", "OpenID Connect Authorization code flow"),
        ],
        string="Auth Flow",
        required=True,
        default="oauth2",
    )

    image_icon_url = fields.Text()

    validation_endpoint = fields.Char(required=False)
    token_endpoint = fields.Char()
    jwks_uri = fields.Char("JWKS URL")
    jwt_assertion_aud = fields.Char(
        "Client Assertion JWT Aud Claim",
        help="Leave blank to use token endpoint for Client Assertion Aud.",
    )

    client_authentication_method = fields.Selection(
        [
            ("client_secret_basic", "Client Secret (Basic)"),
            ("client_secret_post", "Client Secret (Post)"),
            # ("client_secret_jwt", "Signed Client Secret (JWT)"), # Not implemented
            ("private_key_jwt", "Private Key JWT"),
            ("none", "None"),
        ],
        required=True,
        default="client_secret_post",
    )
    client_secret = fields.Char()
    client_private_key = fields.Binary(attachment=False)

    code_verifier = fields.Char("PKCE Code Verifier", default=lambda self: secrets.token_urlsafe(32))

    token_map = fields.Char(
        default=(
            "sub:user_id "
            "name:name "
            "email:email "
            "phone_number:phone "
            "birthdate:birthdate "
            "gender:gender "
            "address:address "
            "picture:picture "
            "groups:groups"
        )
    )

    extra_authorize_params = fields.Text(
        help="Extra Parameters to be passed to Auth endpoint. "
        'To be given as JSON. Example: {"param":"value"}',
    )

    verify_at_hash = fields.Boolean("Verify Access Token Hash", default=True)

    date_format = fields.Char(
        help="Format to be used to parse dates returned by this OIDC Provider",
        default="%Y/%m/%d",
    )

    allow_signup = fields.Selection(
        [
            ("yes", "Allows user signup"),
            ("no", "Denies user signup (invitation only)"),
            ("system_default", "Use System settings for signup"),
        ],
        default="yes",
    )
    signup_default_groups = fields.Many2many("res.groups")
    sync_user_groups = fields.Selection(
        [
            ("on_login", "On every Login"),
            ("on_reset", "When user groups are reset"),
            ("never", "Never"),
        ],
        default="on_reset",
    )
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company.id)

    def oidc_get_tokens(self, params, **kw):
        self.ensure_one()
        if self.flow == "oidc_auth_code":
            access_token, id_token = self._oidc_get_tokens_auth_code_flow(params, **kw)
        elif self.flow == "oidc_implicit":
            access_token, id_token = self._oidc_get_tokens_implicit_flow(params, **kw)
        else:
            # TBD
            access_token, id_token = (None, None)

        if not access_token:
            _logger.error("No access_token in response.")
            raise AccessDenied()
        if not id_token:
            _logger.error("No id_token in response.")

        params["access_token"] = access_token
        params["id_token"] = id_token

        self.verify_access_token(params, **kw)
        if id_token:
            self.verify_id_token(params, **kw)
        return access_token, id_token

    def _oidc_get_tokens_implicit_flow(self, params):
        # Access token and id_token will already be available in params
        return params.get("access_token"), params.get("id_token")

    def _oidc_get_tokens_auth_code_flow(self, params, oidc_redirect_uri=None):
        code = params.get("code")
        if not oidc_redirect_uri:
            oidc_redirect_uri = request.httprequest.base_url

        if self.client_authentication_method == "none":
            token_request_data = dict(
                client_id=self.client_id,
                grant_type="authorization_code",
                code=code,
                code_verifier=self.code_verifier,
                redirect_uri=oidc_redirect_uri,
            )
            response = requests.post(self.token_endpoint, data=token_request_data, timeout=10)
            response.raise_for_status()
            response_json = response.json()
            return response_json.get("access_token"), response_json.get("id_token")
        if self.client_authentication_method == "client_secret_basic":
            token_request_auth = (self.client_id, self.client_secret)
            token_request_data = dict(
                client_id=self.client_id,
                grant_type="authorization_code",
                code=code,
                code_verifier=self.code_verifier,
                redirect_uri=oidc_redirect_uri,
            )
            response = requests.post(
                self.token_endpoint,
                auth=token_request_auth,
                data=token_request_data,
                timeout=10,
            )
            response.raise_for_status()
            response_json = response.json()
            return response_json.get("access_token"), response_json.get("id_token")
        if self.client_authentication_method == "client_secret_post":
            token_request_data = dict(
                client_id=self.client_id,
                client_secret=self.client_secret,
                grant_type="authorization_code",
                code=code,
                code_verifier=self.code_verifier,
                redirect_uri=oidc_redirect_uri,
            )
            response = requests.post(self.token_endpoint, data=token_request_data, timeout=10)
            response.raise_for_status()
            response_json = response.json()
            return response_json.get("access_token"), response_json.get("id_token")
        if self.client_authentication_method == "private_key_jwt":
            private_key_jwt = self.oidc_create_private_key_jwt()
            token_request_data = dict(
                client_id=self.client_id,
                client_assertion_type="urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                client_assertion=private_key_jwt,
                grant_type="authorization_code",
                code=code,
                code_verifier=self.code_verifier,
                redirect_uri=oidc_redirect_uri,
            )
            response = requests.post(self.token_endpoint, data=token_request_data, timeout=10)
            response.raise_for_status()
            response_json = response.json()
            return response_json.get("access_token"), response_json.get("id_token")
        return None

    def oidc_create_private_key_jwt(self):
        secret = base64.b64decode(self.with_context(bin_size=False).client_private_key)
        token = jwt.encode(
            {
                "iss": self.client_id,
                "sub": self.client_id,
                "aud": self.jwt_assertion_aud or self.token_endpoint,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
                "iat": datetime.now(timezone.utc),
            },
            secret,
            algorithm="RS256",
        )
        return token

    @tools.ormcache("self.jwks_uri")
    def oidc_get_jwks(self, **kw):
        r = requests.get(self.jwks_uri, timeout=10)
        r.raise_for_status()
        response = r.json()
        return response

    @api.model
    def oidc_get_response_type(self, flow):
        if flow == "oidc_auth_code":
            return "code"
        elif flow == "oidc_implicit":
            return "id_token token"
        else:
            return "token"

    def oidc_get_validation_dict(self, params):
        self.ensure_one()
        access_token = params.get("access_token")
        id_token = params.get("id_token")
        validation = self.env["res.users"]._auth_oauth_validate(self.id, access_token)
        validation = self.combine_tokens(access_token, id_token, validation)
        validation = self.map_validation_values(validation, params)
        return validation

    def verify_access_token(self, params, **kw):
        self.ensure_one()
        access_token = params.get("access_token")
        jwt.decode(
            access_token,
            self.oidc_get_jwks(**kw),
            options={
                "verify_aud": False,
            },
        )
        return access_token

    def verify_id_token(self, params, **kw):
        self.ensure_one()
        access_token = params.get("access_token")
        id_token = params.get("id_token")
        jwt.decode(
            id_token,
            self.oidc_get_jwks(**kw),
            audience=self.client_id,
            access_token=access_token,
            options={
                "verify_at_hash": self.verify_at_hash,
                "verify_aud": False,
            },
        )
        return id_token

    def map_validation_values(self, validation, params):
        res = {}
        if self.token_map and self.token_map.strip():
            if self.token_map.endswith("*:*"):
                res = validation
            for pair in self.token_map.strip().split(" "):
                if pair:
                    from_key, to_key = (k.strip() for k in pair.split(":", 1))
                    res[to_key] = validation.get(from_key, "")
        return res

    def oidc_signin_create_user(self, validation, params, oauth_partner=None, access_denied_exception=None):
        self.oidc_signin_generate_user_values(validation, params, oauth_partner=oauth_partner)
        if self.allow_signup == "system_default":
            state = json.loads(params["state"])
            token = state.get("t")
            try:
                login, _ = self.env["res.users"].signup(validation, token)
                return login
            except (SignupError, UserError) as e:
                if not access_denied_exception:
                    access_denied_exception = AccessDenied("OIDC Signup failed!")
                raise access_denied_exception from e
        elif self.allow_signup == "yes":
            try:
                if (not validation.get("groups_id")) and self.signup_default_groups:
                    validation["groups_id"] = [(4, group.id) for group in self.signup_default_groups]
                new_user = self.env["res.users"].create(validation)
                return new_user.login
            except Exception as e:
                if not access_denied_exception:
                    access_denied_exception = AccessDenied("OIDC Signup failed!")
                raise access_denied_exception from e
        # elif self.allow_signup == "no":
        else:
            if not access_denied_exception:
                access_denied_exception = AccessDenied("OIDC Signup failed!")
            raise access_denied_exception

    def oidc_signin_find_existing_partner(self, validation, params):
        """
        Should return partner object if already exists.
        Supposed to be overriden by child classes.
        """
        return False

    def oidc_signin_update_userinfo(self, validation, params, oauth_partner=None, oauth_user=None):
        if oauth_user.oidc_userinfo_reset:
            self.oidc_signin_generate_user_values(
                validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user, create_user=False
            )
            oauth_partner.write(validation)
            oauth_user.oidc_userinfo_reset = False

    def oidc_signin_update_groups(self, validation, params, oauth_partner=None, oauth_user=None):
        if self.sync_user_groups == "on_login" or (
            self.sync_user_groups == "on_reset" and oauth_user.oidc_groups_reset
        ):
            self.oidc_signin_process_groups(
                validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user
            )
            groups = validation.get("groups_id")
            if groups:
                oauth_user.groups_id = [(5,)] + groups
                oauth_user.oidc_groups_reset = False

    def oidc_signin_generate_user_values(
        self, validation, params, oauth_partner=None, oauth_user=None, create_user=True
    ):
        self.oidc_signin_process_email(validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user)
        self.oidc_signin_process_login(validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user)
        self.oidc_signin_process_groups(
            validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user
        )

        if not oauth_partner:
            oauth_partner = self.oidc_signin_find_existing_partner(validation, params)
        if oauth_partner and create_user:  # If a partner exists but the user needs to be created.
            new_validation = {
                "login": validation["login"],
                "groups_id": validation.get("groups_id", []),
                "partner_id": oauth_partner.id,
                "oauth_provider_id": self.id,
                "oauth_uid": validation["user_id"],
                "oauth_access_token": params["access_token"],
                "active": True,
            }
            validation.clear()
            validation.update(new_validation)
            return validation

        self.oidc_signin_process_name(validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user)
        self.oidc_signin_process_gender(
            validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user
        )
        self.oidc_signin_process_birthdate(
            validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user
        )
        self.oidc_signin_process_phone(validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user)
        self.oidc_signin_process_picture(
            validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user
        )
        self.oidc_signin_process_other_fields(
            validation, params, oauth_partner=oauth_partner, oauth_user=oauth_user
        )

        if create_user:  # Only for new user creation.
            validation.update(
                {
                    "oauth_provider_id": self.id,
                    "oauth_uid": validation.pop("user_id"),
                    "oauth_access_token": params["access_token"],
                    "active": True,
                }
            )
        return validation

    def oidc_signin_process_login(self, validation, params, oauth_partner=None, oauth_user=None):
        oauth_uid = validation["user_id"]
        if "login" not in validation:
            validation["login"] = validation.get("email", f"provider_{self.id}_user_{oauth_uid}")
        return validation

    def oidc_signin_process_name(self, validation, params, oauth_partner=None, oauth_user=None):
        if "name" not in validation:
            validation["name"] = validation.get("email")
        return validation

    def oidc_signin_process_gender(self, validation, params, oauth_partner=None, oauth_user=None):
        gender = validation.get("gender", "").capitalize()
        if gender:
            validation["gender"] = gender
        return validation

    def oidc_signin_process_birthdate(self, validation, params, oauth_partner=None, oauth_user=None):
        birthdate = validation.get("birthdate")
        if birthdate:
            validation["birthdate"] = datetime.strptime(birthdate, self.date_format).date()
        elif "birthdate" in validation:
            validation.pop("birthdate")
        return validation

    def oidc_signin_process_email(self, validation, params, oauth_partner=None, oauth_user=None):
        if "email" not in validation:
            validation["email"] = None
        return validation

    def oidc_signin_process_phone(self, validation, params, oauth_partner=None, oauth_user=None):
        return validation

    def oidc_signin_process_picture(self, validation, params, oauth_partner=None, oauth_user=None):
        picture = validation.pop("picture", None)
        if picture:
            with urlopen(picture, timeout=20) as response:
                validation["image_1920"] = base64.b64encode(response.read())
        return validation

    def oidc_signin_process_groups(self, validation, params, oauth_partner=None, oauth_user=None):
        """
        Order of checking groups is groups_id, groups, roles
        """
        groups = None
        if "groups_id" in validation:
            groups = validation.pop("groups_id")
        elif "groups" in validation:
            groups = validation.pop("groups")
        elif "roles" in validation:
            groups = validation.pop("roles")
        if groups:
            group_ids = self.env["res.groups"].sudo().search([("full_name", "in", groups)]).ids
            validation["groups_id"] = [(4, group_id) for group_id in group_ids]
        return validation

    def oidc_signin_process_other_fields(self, validation, params, oauth_partner=None, oauth_user=None):
        fields_model = "res.partner" if oauth_partner else "res.users"
        for key in list(validation):
            if key in self.env[fields_model]._fields or key in ("user_id",):
                value = validation[key]
            else:
                validation.pop(key)
            if isinstance(self.env[fields_model]._fields.get(key), fields._String) and isinstance(
                value, dict | list
            ):
                validation[key] = json.dumps(value)
        if self.company_id and validation.get("company_id") != self.company_id.id:
            validation["company_id"] = self.company_id.id
        return validation

    @api.model
    def list_providers(
        self,
        domain=(("enabled", "=", True),),
        redirect=None,
        base_url=None,
        oidc_redirect_uri="/auth_oauth/signin",
        db_name=None,
        **kw,
    ):
        if base_url is None:
            base_url = request.httprequest.url_root.rstrip("/")
        if db_name is None:
            db_name = request.session.db
        if redirect is None:
            redirect = request.params.get("redirect") or "/web"
        if not redirect.startswith(("//", "http://", "https://")):
            redirect = base_url + redirect
        if not oidc_redirect_uri.startswith(("//", "http://", "https://")):
            oidc_redirect_uri = base_url + oidc_redirect_uri

        providers = self.search_read(domain)
        for provider in providers:
            state = dict(d=db_name, p=provider["id"], r=url_quote_plus(redirect), **kw)
            params = dict(
                response_type=self.oidc_get_response_type(provider.get("flow")),
                client_id=provider["client_id"],
                redirect_uri=oidc_redirect_uri,
                scope=provider["scope"],
                state=json.dumps(state, separators=(",", ":")),
            )
            flow = provider.get("flow")
            if flow and flow.startswith("oidc"):
                params.update(
                    dict(
                        nonce=secrets.token_urlsafe(),
                        code_challenge=base64.urlsafe_b64encode(
                            hashlib.sha256(provider["code_verifier"].encode("ascii")).digest()
                        ).rstrip(b"="),
                        code_challenge_method="S256",
                    )
                )
            extra_auth_params = json.loads(provider.get("extra_authorize_params") or "{}")
            params.update(extra_auth_params)
            provider["auth_link"] = f"{provider['auth_endpoint']}?{url_encode(params)}"
        return providers

    @api.model
    def combine_token_dicts(self, *token_dicts) -> dict:
        res = None
        for token_dict in token_dicts:
            if token_dict:
                if not res:
                    res = token_dict
                else:
                    res.update(token_dict)
        return res

    @api.model
    def combine_tokens(self, *tokens) -> dict:
        return self.combine_token_dicts(
            *[
                jwt.get_unverified_claims(token) if isinstance(token, str) else token
                for token in tokens
                if token
            ]
        )
