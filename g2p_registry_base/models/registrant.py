# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging
import re
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import OR

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

    related_1_ids = fields.One2many("g2p.reg.rel", "destination", "Related to registrant 1")
    related_2_ids = fields.One2many("g2p.reg.rel", "source", "Related to registrant 2")

    phone_number_ids = fields.One2many("g2p.phone.number", "partner_id", "Phone Numbers")

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    registration_date = fields.Date(default=lambda self: fields.Date.today())
    tags_ids = fields.Many2many("g2p.registrant.tags", string="Tags")
    civil_status = fields.Char(string="CivilState")
    occupation = fields.Char()
    income = fields.Float()
    district = fields.Many2one("g2p.district")

    @api.onchange("phone_number_ids")
    def phone_number_ids_change(self):
        phone = ""
        if self.phone_number_ids:
            phone = ",".join(
                [p for p in self.phone_number_ids.filtered(lambda rec: not rec.disabled).mapped("phone_no")]
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
                    error_message = "Registration date must be less than the current date."
                    raise ValidationError(error_message)
                elif (
                    "birthdate" in record and record.birthdate and record.registration_date < record.birthdate
                ):
                    error_message = "Registration date must be later than the birth date."
                    raise ValidationError(error_message)

    @api.constrains("phone")
    def _onchange_phone_validation(self):
        for rec in self:
            rec._validate_phone(rec.phone, _("Invalid phone number!"))

    @api.constrains("mobile")
    def _onchange_mobile_validation(self):
        for rec in self:
            rec._validate_phone(rec.mobile, _("Invalid mobile number!"))

    def _validate_phone(self, number, error_message):
        PHONE_REGEX = self.env["ir.config_parameter"].get_param("g2p_registry.phone_regex")
        if PHONE_REGEX and number and not re.match(PHONE_REGEX, number):
            raise ValidationError(error_message)

    def unlink(self):
        res = super().unlink()
        # Preventing delete access for registrar role
        # Requirement needs contact creation access
        # only way to do because conflict happen due to contact creation access
        group_g2p_registrar = self.env.user.has_group("g2p_registry_base.group_g2p_registrar")
        group_g2p_admin = self.env.user.has_group("g2p_registry_base.group_g2p_admin")
        if group_g2p_registrar and not (group_g2p_admin or self.env.user._is_admin()):
            raise UserError(
                _(
                    "You do not have the necessary permissions to delete partner records. "
                    "Please contact the administrator."
                )
            )
        return res

    def _check_company_domain(self, companies):
        """Overrides the default domain to include the default company that was setup in company_id field.

        This is to fix the issue that is occuring when the user is trying to create a new company in an
        instance that has "stock" module and "g2p_registry_base" module installed. The issue is that the
        `_check_company` function checks if the company of the record is either
        False or the same with the record's company.

        To replicate the issue:
        1. Install the "stock" module and "g2p_registry_base" module.
        2. Create a new company.
        3. "Incompatible companies on records" error should not occur.
        """

        domain = super()._check_company_domain(companies)
        domain = OR([domain, [("company_id", "=", self.env.company.id)]])
        return domain
