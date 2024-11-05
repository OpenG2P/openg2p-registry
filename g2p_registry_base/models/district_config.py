# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class G2PDistrict(models.Model):
    _name = "g2p.district"
    _description = "G2P District"
    _order = "name ASC"

    name = fields.Char()
    code = fields.Char()
    state_id = fields.Many2one("res.country.state")
