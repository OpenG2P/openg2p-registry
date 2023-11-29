# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models
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
    def _check_name(self):
        group_types = self.search([])
        for record in self:
            if not record.name:
                error_message = _("kind should not empty.")
                raise ValidationError(error_message)
        for record in group_types:
            if self.name.lower() == record.name.lower() and self.id != record.id:
                raise ValidationError(_("kind already exists"))
