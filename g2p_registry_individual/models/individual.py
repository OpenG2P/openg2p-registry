# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2PIndividual(models.Model):
    _inherit = "res.partner"

    def _get_dynamic_selection(self):
        options = self.env["gender.type"].search([])
        return [(option.value, option.code) for option in options]

    family_name = fields.Char(translate=False)
    given_name = fields.Char(translate=False)
    addl_name = fields.Char("Additional Name", translate=False)
    birth_place = fields.Char()
    birthdate_not_exact = fields.Boolean("Approximate Birthdate")
    birthdate = fields.Date("Date of Birth")
    age = fields.Char(compute="_compute_calc_age", size=50, readonly=True)
    gender = fields.Selection(selection=_get_dynamic_selection)

    @api.onchange("is_group", "family_name", "given_name", "addl_name")
    def name_change(self):
        vals = {}
        if not self.is_group:
            name = ""
            if self.family_name:
                name += self.family_name + ", "
            if self.given_name:
                name += self.given_name + " "
            if self.addl_name:
                name += self.addl_name + " "
            vals.update({"name": name.upper()})
            self.update(vals)

    @api.depends("birthdate")
    def _compute_calc_age(self):
        for line in self:
            line.age = self.compute_age_from_dates(line.birthdate)

    def compute_age_from_dates(self, partner_dob):
        now = datetime.strptime(str(fields.Datetime.now())[:10], "%Y-%m-%d")
        if partner_dob:
            dob = partner_dob
            delta = relativedelta(now, dob)
            # years_months_days = str(delta.years) +"y "+ str(delta.months) +"m "+ str(delta.days)+"d"
            years_months_days = str(delta.years)
        else:
            years_months_days = "No Birthdate!"
        return years_months_days

    @api.constrains("birthdate")
    def _check_birthdate(self):
        for record in self:
            if record.birthdate and record.birthdate > date.today():
                error_message = "Birth date must be on or before the current date."
                raise ValidationError(error_message)
