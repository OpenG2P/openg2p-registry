from odoo import api, fields, models
from odoo.tools import safe_eval


class RegistryEncryptionProvider(models.Model):
    _inherit = "g2p.encryption.provider"

    registry_fields_to_enc = fields.Text(
        "Registry Fields to Encrypt",
        default="""[
            "name",
            "family_name",
            "given_name",
            "addl_name",
            "display_name",
            "address",
            "birth_place",
        ]""",
    )

    registry_enc_field_placeholder = fields.Char("Registry Encrypted Field Placeholder", default="encrypted")

    def get_registry_fields_set_to_enc(self):
        self.ensure_one()
        return set(safe_eval.safe_eval(self.registry_fields_to_enc))

    @api.model
    def set_registry_provider(self, provider_id, replace=True):
        if provider_id and (
            replace
            or not self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry_encryption.encryption_provider_id", None)
        ):
            self.env["ir.config_parameter"].sudo().set_param(
                "g2p_registry_encryption.encryption_provider_id", str(provider_id)
            )

    @api.model
    def get_registry_provider(self):
        prov_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry_encryption.encryption_provider_id", None)
        )
        return self.sudo().browse(int(prov_id)) if prov_id else None
