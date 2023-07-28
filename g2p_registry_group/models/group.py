# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2PGroup(models.Model):
    _inherit = "res.partner"

    kind = fields.Many2one("g2p.group.kind")
    is_partial_group = fields.Boolean("Partial Group")
    kind_as_str = fields.Char(related="kind.name")


class G2PGroupKind(models.Model):
    _name = "g2p.group.kind"
    _description = "Group Kind"
    _order = "id desc"

    name = fields.Char("Kind")

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
