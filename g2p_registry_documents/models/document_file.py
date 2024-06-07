from odoo import fields, models


class G2PDocumentRegistry(models.Model):
    _inherit = "storage.file"

    registrant_id = fields.Many2one("res.partner")

    def get_record(self):
        for record in self:
            return {
                "mimetype": record.mimetype,
                "name": record.name,
                "url": record.url if record.url else "#",
            }
