from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    g2p_registry_documents_store = fields.Many2one(
        "storage.backend",
        config_parameter="g2p_registry_documents.document_store",
    )
