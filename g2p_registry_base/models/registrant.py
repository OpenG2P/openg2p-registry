# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    # Custom Fields
    address = fields.Text()
    district = fields.Char()
    postal = fields.Char()
    full_address = fields.Text(compute="_compute_address", string="Address")
    disabled = fields.Datetime("Date Disabled")
    disabled_reason = fields.Text("Reason for disabling")
    disabled_by = fields.Many2one("res.users")

    reg_ids = fields.One2many("g2p.reg.id", "partner_id", "Registrant IDs")
    is_registrant = fields.Boolean("Registrant")
    is_group = fields.Boolean("Group")

    name = fields.Char(index=True, translate=True)

    related_1_ids = fields.One2many(
        "g2p.reg.rel", "registrant2", "Related to registrant 1"
    )
    related_2_ids = fields.One2many(
        "g2p.reg.rel", "registrant1", "Related to registrant 2"
    )

    phone_number_ids = fields.One2many(
        "g2p.phone.number", "partner_id", "Phone Numbers"
    )

    registration_date = fields.Date()

    @api.depends("address", "district", "postal")
    def _compute_address(self):
        for rec in self:
            rec.full_address = ""
            if rec.district:
                rec.full_address = rec.district
            if rec.address:
                rec.full_address += " " + rec.address
            if rec.postal:
                rec.full_address += " " + rec.postal

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
