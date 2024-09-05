from odoo import fields, models


class RegistryEncryptConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    registry_encryption_provider = fields.Many2one(
        "g2p.encryption.provider",
        config_parameter="g2p_registry_encryption.encryption_provider_id",
    )
    encrypt_registry = fields.Boolean(config_parameter="g2p_registry_encryption.encrypt_registry")

    # TODO: Change this to user context
    decrypt_registry = fields.Boolean(config_parameter="g2p_registry_encryption.decrypt_registry")
