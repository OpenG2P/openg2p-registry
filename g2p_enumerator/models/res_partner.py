# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    enumerator_ids = fields.One2many("g2p.enumerator","partner_id")
