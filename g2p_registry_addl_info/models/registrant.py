from odoo import models

from odoo.addons.g2p_json_field.models import json_field


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    additional_g2p_info = json_field.JSONField("Additional Information", default={})
