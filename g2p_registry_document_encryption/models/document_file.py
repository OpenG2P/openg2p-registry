import base64

from odoo import fields, models


class G2PDocumentRegistry(models.Model):
    _inherit = "storage.file"

    is_encrypted = fields.Boolean(string="Encrypted", default=False)

    def _inverse_data(self):
        for record in self:
            record.write(record._prepare_meta_for_file())
            if not record.mimetype:
                binary_data = base64.b64decode(record.data)
                mime = self._get_mime_type(binary_data)
                record.mimetype = mime

            is_encrypt_fields = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("g2p_registry_encryption.encrypt_registry", default=False)
            )

            if is_encrypt_fields and record.registrant_id:
                record.is_encrypted = True

            record.backend_id.sudo().add(
                record.relative_path,
                record.data,
                mimetype=record.mimetype,
                binary=False,
                registrant_id=record.registrant_id.id,
            )
