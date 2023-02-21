from odoo import models

from . import json_field


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    additional_g2p_info = json_field.JSONField("Additional Information", default={})
