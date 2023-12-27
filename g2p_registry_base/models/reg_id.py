# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class G2PRegistrantID(models.Model):
    _name = "g2p.reg.id"
    _description = "Registrant ID"
    _order = "id desc"

    partner_id = fields.Many2one(
        "res.partner",
        "Registrant",
        required=True,
        domain=[("is_registrant", "=", True)],
    )
    id_type = fields.Many2one("g2p.id.type", "ID Type", required=True)
    value = fields.Char(size=100)

    expiry_date = fields.Date()
    id_type_as_str = fields.Char(related="id_type.name")

    def _compute_display_name(self):
        res = super()._compute_display_name()
        for rec in self:
            name = ""
            if rec.partner_id:
                name = rec.partner_id.name
            rec.display_name = name
        return res

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=100, order=None):
        domain = domain or []
        if name:
            domain = [("partner_id", operator, name)] + domain
        return self._search(domain, limit=limit, order=order)

    @api.constrains("value")
    @api.onchange("value")
    def _onchange_id_validation(self):
        for rec in self:
            if not rec.value:
                return
            if rec.id_type.id_validation:
                if not re.match(rec.id_type.id_validation, rec.value):
                    raise ValidationError(
                        f"The provided {rec.id_type.name} ID '{rec.value}' is invalid."
                    )


class G2PIDType(models.Model):
    _name = "g2p.id.type"
    _description = "ID Type"
    _order = "name ASC"

    name = fields.Char()
    id_validation = fields.Char()

    @api.constrains("name")
    def _check_name(self):
        id_types = self.search([])
        for record in self:
            if not record.name:
                error_message = _("Id type should not empty.")
                raise ValidationError(error_message)
        for record in id_types:
            if self.name.lower() == record.name.lower() and self.id != record.id:
                raise ValidationError(_("Id type already exists"))
