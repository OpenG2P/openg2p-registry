# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ChangeReason(models.Model):
    _name = "g2p.change.reason"
    _description = "Change Reason"
    _order = "name"

    name = fields.Char(string="Reason", required=True)
    active = fields.Boolean(default=True)

    @api.constrains("name")
    def _check_name_unique(self):
        """Ensure change reason names are unique."""
        for record in self:
            existing = self.search([("name", "=", record.name), ("id", "!=", record.id)])
            if existing:
                raise ValidationError(
                    _("Change reason '%s' already exists." " Please use a unique name.") % record.name
                )
