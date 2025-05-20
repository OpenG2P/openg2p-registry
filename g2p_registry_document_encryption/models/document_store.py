from odoo import api, fields, models


class G2PDocumentStore(models.Model):
    _inherit = "storage.backend"

    encryption_strategy = fields.Selection(
        selection_add=[("registry_based", "Use Registry Encryption Settings")]
    )

    viewing_decryption_strategy = fields.Selection(
        selection_add=[("registry_based", "Use Registry Encryption Settings")]
    )

    def get_encryption_provider(self):
        self.ensure_one()
        if self.encryption_strategy == "registry_based":
            is_encrypt_registry = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("g2p_registry_encryption.encrypt_registry", default=False)
            )
            if is_encrypt_registry:
                prov = self.env["g2p.encryption.provider"].get_registry_encryption_provider()
                return prov if prov else None
            else:
                return None
        return super().get_encryption_provider()

    def get_decryption_provider(self):
        self.ensure_one()
        if self.viewing_decryption_strategy == "registry_based":
            is_decrypt_registry = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("g2p_registry_encryption.decrypt_registry", default=False)
            )
            if is_decrypt_registry:
                prov = self.env["g2p.encryption.provider"].get_registry_encryption_provider()
                return prov if prov else None
            else:
                return None
        return super().get_decryption_provider()

    @api.model
    def set_encryption_stragies_to_registry(self, record_ids):
        records = self.browse(record_ids)
        records.write(
            {"encryption_strategy": "registry_based", "viewing_decryption_strategy": "registry_based"}
        )
