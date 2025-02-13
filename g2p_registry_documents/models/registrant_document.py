from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    supporting_documents_ids = fields.One2many("storage.file", "registrant_id")

    @api.model
    def get_registry_documents_store(self):
        doc_store_id_str = (
            self.env["ir.config_parameter"].sudo().get_param("g2p_registry_documents.document_store")
        )
        if not doc_store_id_str:
            return None
        return self.env["storage.backend"].sudo().browse(int(doc_store_id_str))
