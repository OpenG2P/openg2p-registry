# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from schwifty import IBAN

from odoo import api, fields, models


class G2PBanks(models.Model):
    _inherit = "res.partner.bank"

    iban = fields.Char(compute="_compute_account_number", string="IBAN")

    @api.depends("acc_number", "bank_id")
    def _compute_account_number(self):
        for rec in self:
            rec.iban = ""
            if rec.bank_id and rec.bank_id.country and rec.acc_number:
                rec.iban = IBAN.generate(
                    rec.bank_id.country.code,
                    bank_code=rec.bank_id.bic,
                    account_code=rec.acc_number,
                )
