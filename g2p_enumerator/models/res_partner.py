# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    enumerator_id = fields.Many2one("g2p.enumerator")
    enumerator_user_id = fields.Char(related="enumerator_id.enumerator_user_id")

    data_collection_date = fields.Date(related="enumerator_id.data_collection_date")
