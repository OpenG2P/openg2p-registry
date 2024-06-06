import base64

import magic

from odoo import fields, models


class G2PDocumentRegistry(models.Model):
    _inherit = "storage.file"

    registrant_id = fields.Many2one("res.partner")

    attachment_id = fields.Many2one("ir.attachment", string="Attachment")

    storage_file_type = fields.Char(string="File Type")

    def get_binary(self):
        for record in self:
            if not record.attachment_id:
                data = record.data
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": "Preview File",
                        "datas": data,
                        "res_model": self._name,
                        "res_id": record.id,
                        "type": "binary",
                    }
                )
                record.attachment_id = attachment.id

            return {
                "id": record.attachment_id.id,
                "mimetype": record.attachment_id.mimetype,
                "index_content": record.attachment_id.index_content,
                "url": record.url if record.url else "#",
            }

    def create(self, vals):
        if isinstance(vals, dict):
            file_type = self._get_file_type(vals)
            vals["storage_file_type"] = file_type
        elif isinstance(vals, list):
            for i in range(len(vals)):
                vals_obj = vals[i]
                file_type = self._get_file_type(vals_obj)
                vals[i]["storage_file_type"] = file_type

        return super().create(vals)

    def _get_file_type(self, vals_obj):
        document_data = vals_obj.get("data", None)
        if document_data:
            decoded_data = base64.b64decode(document_data)
            magic_obj = magic.Magic()
            file_type = magic_obj.from_buffer(decoded_data)
            if "," in file_type:
                file_type = file_type.split(",")[0].strip()
            return file_type
