# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from random import randint

from odoo import fields, models


class G2PRegistrantTags(models.Model):
    _name = "g2p.registrant.tags"
    _description = "Registrant Tags"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Tags", required=True)
    color = fields.Integer(default=_get_default_color)
    active = fields.Boolean(
        default=True, help="Archive to hide the RegistrantTag without removing it."
    )
