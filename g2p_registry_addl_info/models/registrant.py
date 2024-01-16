from odoo import fields, models


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    additional_g2p_info = fields.Json("Additional Information", default={})
