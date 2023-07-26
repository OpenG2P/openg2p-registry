# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging
import re
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    # Custom Fields
    address = fields.Text()
    disabled = fields.Datetime("Date Disabled")
    disabled_reason = fields.Text("Reason for Disabling")
    disabled_by = fields.Many2one("res.users")

    reg_ids = fields.One2many("g2p.reg.id", "partner_id", "Registrant IDs")
    is_registrant = fields.Boolean("Registrant")
    is_group = fields.Boolean("Group")

    name = fields.Char(index=True)

    related_1_ids = fields.One2many(
        "g2p.reg.rel", "destination", "Related to registrant 1"
    )
    related_2_ids = fields.One2many("g2p.reg.rel", "source", "Related to registrant 2")

    phone_number_ids = fields.One2many(
        "g2p.phone.number", "partner_id", "Phone Numbers"
    )

    registration_date = fields.Date(default=lambda self: fields.Date.today())
    tags_ids = fields.Many2many("g2p.registrant.tags", string="Tags")
    civil_status = fields.Char(string="CivilState")
    occupation = fields.Char()
    income = fields.Float()
    district = fields.Char()

    @api.onchange("phone_number_ids")
    def phone_number_ids_change(self):
        phone = ""
        if self.phone_number_ids:
            phone = ",".join(
                [
                    p
                    for p in self.phone_number_ids.filtered(
                        lambda rec: not rec.disabled
                    ).mapped("phone_no")
                ]
            )
        self.phone = phone

    def enable_registrant(self):
        for rec in self:
            if rec.disabled:
                rec.update(
                    {
                        "disabled": None,
                        "disabled_by": None,
                        "disabled_reason": None,
                    }
                )

    @api.onchange("income")
    def _onchange_negative_restrict(self):
        res = {}
        if self.income < 0:
            res["warning"] = {
                "title": "Warning",
                "message": "Negative values are not allowed.",
            }
            res["value"] = {"income": 0}
        return res

    @api.constrains("registration_date")
    def _check_registration_date(self):
        for record in self:
            if record.registration_date:
                if record.registration_date > date.today():
                    error_message = (
                        "Registration date must be less than the current date."
                    )
                    raise ValidationError(error_message)
                elif record.birthdate and record.registration_date < record.birthdate:
                    error_message = (
                        "Registration date must be less than the birth date."
                    )
                    raise ValidationError(error_message)

    @api.constrains("phone_number_ids")
    def _check_phone_number_validation(self):
        PHONE_REGEX = self.env["ir.config_parameter"].get_param(
            "g2p_registry.phone_regex"
        )
        if not PHONE_REGEX:
            return
        for rec in self.phone_number_ids:
            if rec.phone_no and not re.match(PHONE_REGEX, rec.phone_no):
                raise models.ValidationError(_("Invalid phone number!"))
