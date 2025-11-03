# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class G2PRegion(models.Model):
    _name = "g2p.region"
    _description = "G2P Region"

    name = fields.Char()
    code = fields.Char()
    iso_code = fields.Char()
