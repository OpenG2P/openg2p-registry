from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    supporting_documents_ids = fields.One2many("storage.file", "registrant_id")
