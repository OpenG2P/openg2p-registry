from odoo import fields, models


class G2PDocumentRegistry(models.Model):
    _inherit = "storage.file"

    registrant_id = fields.Many2one("res.partner", index=True)

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        for key in fields_list:
            if key == "backend_id" and self._context.get("registry_documents", False):
                res[key] = self.env["res.partner"].get_registry_documents_store()
        return res
