# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    enumerator_id = fields.Many2one("g2p.enumerator")
    enumerator_user_id = fields.Char(related="enumerator_id.enumerator_user_id")

    data_collection_date = fields.Date(related="enumerator_id.data_collection_date")

    eid = fields.Char(string="EID", copy=False, readonly=True, index=True)
    creator_eid = fields.Char(string="Creator's EID", compute="_compute_creator_eid")

    @api.model
    def create(self, vals):
        if not vals.get("eid"):
            vals["eid"] = "New"
        res = super(G2PRegistrant, self).create(vals)
        if res.eid == "New" and res.supplier_rank > 0:
            res.eid = res.generate_eid()
        return res

    def generate_eid(self):
        return self.env["ir.sequence"].next_by_code("enumeratorCode") or "New"

    @api.depends("create_uid")
    def _compute_creator_eid(self):
        for partner in self:
            if partner.create_uid:
                creator = partner.create_uid.partner_id
                partner.creator_eid = creator.eid if creator else False
            else:
                partner.creator_eid = False
