import logging
from datetime import datetime, timedelta

from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    client_authentication_method = fields.Selection(
        selection_add=[
            ("private_key_jwt_enc_provider", "Private Key JWT - Encryption Provider"),
        ],
        ondelete={"private_key_jwt_enc_provider": "set private_key_jwt"},
    )
    client_private_key_enc_provider = fields.Many2one("g2p.encryption.provider", required=False)

    def oidc_create_private_key_jwt(self, **kw):
        if self.client_authentication_method == "private_key_jwt_enc_provider":
            if not self.client_private_key_enc_provider:
                raise ValidationError(f"Encryption Provider is not set in OauthProvider ID-{self.id}")
            iat = datetime.now()
            exp = iat + timedelta(hours=1)
            return self.client_private_key_enc_provider.jwt_sign(
                {
                    "iss": self.client_id,
                    "sub": self.client_id,
                    "aud": self.jwt_assertion_aud or self.token_endpoint,
                    "exp": int(exp.timestamp()),
                    "iat": int(iat.timestamp()),
                }
            )

        return super().oidc_create_private_key_jwt(**kw)
