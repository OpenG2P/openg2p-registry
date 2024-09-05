from odoo import fields, models


class G2PEncryptionProvider(models.Model):
    _name = "g2p.encryption.provider"
    _description = "G2P Encryption Provider"

    name = fields.Char(required=True)
    type = fields.Selection(selection=[])

    def encrypt_data(self, data: bytes, **kwargs) -> bytes:
        """
        Both input and output are NOT base64 encoded
        """
        try:
            encrypt_func = getattr(self, f"encrypt_data_{self.type}")
        except Exception as e:
            raise NotImplementedError() from e
        return encrypt_func(data, **kwargs)

    def decrypt_data(self, data: bytes, **kwargs) -> bytes:
        """
        Both input and output are NOT base64 encoded
        """
        try:
            decrypt_func = getattr(self, f"decrypt_data_{self.type}")
        except Exception as e:
            raise NotImplementedError() from e
        return decrypt_func(data, **kwargs)

    def jwt_sign(
        self,
        data,
        include_payload=True,
        include_certificate=False,
        include_cert_hash=False,
        **kwargs,
    ) -> str:
        try:
            jwt_func = getattr(self, f"jwt_sign_{self.type}")
        except Exception as e:
            raise NotImplementedError() from e
        return jwt_func(
            data,
            include_payload=True,
            include_certificate=False,
            include_cert_hash=False,
            **kwargs,
        )

    def jwt_verify(self, data: str, **kwargs):
        try:
            jwt_func = getattr(self, f"jwt_verify_{self.type}")
        except Exception as e:
            raise NotImplementedError() from e
        return jwt_func(data, **kwargs)

    def get_jwks(self, **kwargs):
        try:
            jwk_func = getattr(self, f"get_jwks_{self.type}")
        except Exception as e:
            raise NotImplementedError() from e
        return jwk_func(**kwargs)
