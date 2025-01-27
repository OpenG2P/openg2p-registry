from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    g2p_profile_image_document_store = fields.Many2one(
        "storage.backend", config_parameter="g2p_profile_image.image_document_storage"
    )
