from odoo import api, fields, models


class G2PDocumentRegistry(models.Model):
    _inherit = "storage.file"

    is_encrypted = fields.Boolean(string="Encrypted", default=False)

    can_preview_encrypted = fields.Boolean(compute="_compute_can_preview_encrypted")

    def _inverse_data(self):
        for record in self:
            record.write(record._prepare_meta_for_file())

            enc_provider = record.backend_id.get_encryption_provider()

            if enc_provider and record.registrant_id:
                record.is_encrypted = True
                record.data = enc_provider.encrypt_data(record.data)

            record.backend_id.sudo().add(
                record.relative_path,
                record.data,
                mimetype=record.mimetype,
                binary=False,
                registrant_id=record.registrant_id.id,
            )

    @api.depends("backend_id", "relative_path", "file_size", "is_encrypted")
    def _compute_data(self):
        # pylint: disable=missing-return
        super()._compute_data()
        for record in self:
            if record.relative_path and not record._context.get("bin_size"):
                dec_provider = record.backend_id.get_decryption_provider()
                if record.is_encrypted and dec_provider:
                    record.data = dec_provider.decrypt_data(record.data)

    @api.depends("backend_id", "is_encrypted")
    def _compute_can_preview_encrypted(self):
        for rec in self:
            rec.can_preview_encrypted = (not rec.is_encrypted) or (
                rec.is_encrypted and rec.backend_id.get_decryption_provider()
            )
