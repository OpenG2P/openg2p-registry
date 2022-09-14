# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from schwifty import IBAN

from odoo import api, fields, models


class G2PBanks(models.Model):
    _inherit = "res.partner.bank"

    account_code = fields.Char()
    account_number = fields.Char(compute="_compute_account_number")

    @api.depends("account_code", "bank_id")
    def _compute_account_number(self):
        for rec in self:
            rec.account_number = ""
            if rec.bank_id and rec.account_code:
                rec.account_number = IBAN.generate(
                    self.env.user.country_code,
                    bank_code=rec.bank_id.bic,
                    account_code=rec.account_code,
                )
                rec.acc_number = rec.account_number
