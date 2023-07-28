# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import re
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
    def _check_name_no_special_characters(self):
        for record in self:
            # Define a regular expression pattern to allow only alphanumeric characters and underscores
            if record.name:
                pattern = r"^[a-zA-Z0-9_]+$"
                if not re.match(pattern, record.name):
                    error_message = "Name should contain only alphanumeric characters and underscores."
                    raise ValidationError(error_message)
            else:
                error_message = (
                    "Name should contain only alphanumeric characters and underscores."
                )
                raise ValidationError(error_message)
