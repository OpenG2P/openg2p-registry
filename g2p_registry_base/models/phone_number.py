# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

import logging
import re

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class G2PPhoneNumber(models.Model):
    _name = "g2p.phone.number"
    _description = "Phone Number"
    _order = "id desc"
    _rec_name = "phone_no"

    partner_id = fields.Many2one(
        "res.partner",
        "Registrant",
        required=True,
        domain=[("is_registrant", "=", True)],
    )
    phone_no = fields.Char("Phone Number", required=True)
    phone_sanitized = fields.Char(compute="_compute_phone_sanitized", store=True)
    date_collected = fields.Date(
        default=fields.Date.today,
    )
    disabled = fields.Datetime("Date Disabled")
    disabled_by = fields.Many2one("res.users")
    country_id = fields.Many2one("res.country", "Country")

    @api.onchange("date_collected")
    def _check_date_collected(self):
        for record in self:
            if record.date_collected and record.date_collected > fields.Date.today():
                raise exceptions.ValidationError(
                    _("Date collected cannot be in the future.")
                )

    @api.depends("phone_no", "country_id")
    def _compute_phone_sanitized(self):
        for rec in self:
            rec.phone_sanitized = ""
            if rec.phone_no:
                country_fname = "country_id"
                number = rec["phone_no"]
                sanitized = str(
                    self.env.user._phone_format(
                        number=[number],
                        country=country_fname,
                        force_format="E164",
                    )
                )
                rec.phone_sanitized = sanitized

    @api.onchange("phone_no", "country_id")
    def _onchange_phone_validation(self):
        PHONE_REGEX = self.env["ir.config_parameter"].get_param(
            "g2p_registry.phone_regex"
        )
        if not self.phone_no:
            return
        self.phone_no = (
            self._phone_format(fname="phone", force_format="INTERNATIONAL")
            or self.phone
        )
        _logger.debug(f"phone_no: {self.phone_no}")
        if PHONE_REGEX:
            if not re.match(PHONE_REGEX, self.phone_no):
                raise models.ValidationError(_("Invalid phone number!"))

    def disable_phone(self):
        for rec in self:
            if not rec.disabled:
                rec.update(
                    {
                        "disabled": fields.Datetime.now(),
                        "disabled_by": self.env.user,
                    }
                )

    def enable_phone(self):
        for rec in self:
            if rec.disabled:
                rec.update(
                    {
                        "disabled": None,
                        "disabled_by": None,
                    }
                )
