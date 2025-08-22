import logging
import os

from odoo import fields

_logger = logging.getLogger(__name__)

KEYCLOAK_ISSUER_URL = os.getenv("KEYCLOAK_ISSUER_URL", "http://keycloak.your.org/realms/master").rstrip("/")
KEYCLOAK_AUTH_URL = os.getenv(
    "KEYCLOAK_AUTH_URL", f"{KEYCLOAK_ISSUER_URL}/protocol/openid-connect/auth"
).rstrip("/")
KEYCLOAK_TOKEN_URL = os.getenv(
    "KEYCLOAK_TOKEN_URL", f"{KEYCLOAK_ISSUER_URL}/protocol/openid-connect/token"
).rstrip("/")
KEYCLOAK_USERINFO_URL = os.getenv(
    "KEYCLOAK_USERINFO_URL", f"{KEYCLOAK_ISSUER_URL}/protocol/openid-connect/userinfo"
).rstrip("/")
KEYCLOAK_JWKS_URL = os.getenv(
    "KEYCLOAK_JWKS_URL", f"{KEYCLOAK_ISSUER_URL}/protocol/openid-connect/certs"
).rstrip("/")

KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")
KEYCLOAK_TOKEN_MAP = os.getenv(
    "KEYCLOAK_TOKEN_MAP",
    "email:user_id name:name email:email phone_number:phone birthdate:birthdate gender:gender "
    "address:address picture:picture client_roles:groups",
)
KEYCLOAK_PKCE_ENABLED = "false" != os.getenv("KEYCLOAK_PKCE_ENABLED")
KEYCLOAK_VERIFY_AT_HASH_ENABLED = "false" != os.getenv("KEYCLOAK_VERIFY_AT_HASH_ENABLED")
KEYCLOAK_ALLOW_SIGNUP = os.getenv("KEYCLOAK_ALLOW_SIGNUP", "yes")
KEYCLOAK_SYNC_USER_GROUPS = os.getenv("KEYCLOAK_SYNC_USER_GROUPS", "on_login")


def post_init_hook(env):
    keycloak_provider = env["auth.oauth.provider"].create(
        {
            "name": "Keycloak",
            "flow": "oidc_auth_code",
            "token_map": KEYCLOAK_TOKEN_MAP,
            "client_authentication_method": "client_secret_post",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
            "enabled": True,
            "body": "Login with Keycloak",
            "css_class": "fa fa-fw fa-sign-in text-primary",
            "auth_endpoint": KEYCLOAK_AUTH_URL,
            "scope": "openid profile email",
            "validation_endpoint": KEYCLOAK_USERINFO_URL,
            "token_endpoint": KEYCLOAK_TOKEN_URL,
            "jwks_uri": KEYCLOAK_JWKS_URL,
            "enable_pkce": KEYCLOAK_PKCE_ENABLED,
            "verify_at_hash": KEYCLOAK_VERIFY_AT_HASH_ENABLED,
            "allow_signup": KEYCLOAK_ALLOW_SIGNUP,
            "signup_default_groups": [fields.Command.link(env.ref("base.group_user").id)],
            "sync_user_groups": KEYCLOAK_SYNC_USER_GROUPS,
        }
    )
    env["ir.config_parameter"].set_param("auth_oauth.authorization_header", "True")
    env["ir.config_parameter"].set_param(
        "g2p_disable_password_login.direct_oauth_provider",
        str(keycloak_provider.id),
    )
