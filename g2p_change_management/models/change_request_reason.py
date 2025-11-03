# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ChangeReason(models.Model):
    _name = "g2p.change.request.reason"
    _description = "Change Request Reason"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    @api.constrains("name")
    def _check_name_unique(self):
        for record in self:
            existing = self.search([("name", "=", record.name), ("id", "!=", record.id)])
            if existing:
                raise ValidationError(
                    _("Change request reason '%s' already exists." " Please use a unique name.") % record.name
                )
