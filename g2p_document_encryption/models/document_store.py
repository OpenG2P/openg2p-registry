from odoo import fields, models


class G2PDocumentStore(models.Model):
    _inherit = "storage.backend"

    encryption_strategy = fields.Selection(
        selection=[("always_encrypt", "Always Encrypt")],
        required=False,
        help="Leave blank for no encryption",
    )

    viewing_decryption_strategy = fields.Selection(
        selection=[("always_decrypt", "Always Decrypt")],
        required=False,
        help="Whether or not to decrypt document for viewing it. Leave blank to never decrypt documents",
    )

    encryption_provider_id = fields.Many2one("g2p.encryption.provider", required=False)

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {"encryption_strategy": {}, "viewing_decryption_strategy": {}, "encryption_provider_id": {}}
        )
        return env_fields

    def get_encryption_provider(self):
        self.ensure_one()
        if self.encryption_strategy == "always_encrypt":
            return self.encryption_provider_id
        return None

    def get_decryption_provider(self):
        self.ensure_one()
        if self.viewing_decryption_strategy == "always_decrypt":
            return self.encryption_provider_id
        return None
