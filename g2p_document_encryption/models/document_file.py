import base64

from odoo import api, fields, models


class G2PDocumentFile(models.Model):
    _inherit = "storage.file"

    is_encrypted = fields.Boolean(string="Encrypted", default=False)

    can_preview_encrypted = fields.Boolean(compute="_compute_can_preview_encrypted")

    def _inverse_data(self):
        for record in self:
            record.write(record._prepare_meta_for_file())

            enc_provider = record.backend_id.get_encryption_provider()
            dec_provider = record.backend_id.get_decryption_provider()

            decrypted_data = record.data
            encrypted_data = None

            if enc_provider:
                record.is_encrypted = True
                encrypted_data = base64.b64encode(enc_provider.encrypt_data(base64.b64decode(decrypted_data)))
                if not dec_provider:
                    # If decryption is not enabled, the data record.data in cache
                    # will have to be encrypted data.
                    record.data = encrypted_data

            record.backend_id.sudo().add(
                record.relative_path,
                encrypted_data if enc_provider else decrypted_data,
                mimetype=record.mimetype,
                binary=False,
            )

    @api.depends("backend_id", "relative_path", "file_size", "is_encrypted")
    def _compute_data(self):
        # pylint: disable=missing-return
        super()._compute_data()
        for record in self:
            if record.relative_path and not record._context.get("bin_size"):
                dec_provider = record.backend_id.get_decryption_provider()
                if record.is_encrypted and dec_provider:
                    record.data = base64.b64encode(dec_provider.decrypt_data(base64.b64decode(record.data)))

    @api.depends("backend_id", "is_encrypted")
    def _compute_can_preview_encrypted(self):
        for rec in self:
            rec.can_preview_encrypted = (not rec.is_encrypted) or (
                rec.is_encrypted and rec.backend_id.get_decryption_provider()
            )
