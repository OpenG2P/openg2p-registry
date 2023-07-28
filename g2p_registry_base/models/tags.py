# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
from random import randint

from odoo import api, fields, models
from odoo.exceptions import ValidationError


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

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if not record.name:
                error_message = "Tag name should not empty."
                raise ValidationError(error_message)
