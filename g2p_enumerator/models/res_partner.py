# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    enumerator_id = fields.Many2one("g2p.enumerator")
    enumerator_user_id = fields.Char(related="enumerator_id.enumerator_user_id")

    data_collection_date = fields.Date(related="enumerator_id.data_collection_date")

    eid = fields.Char(string="EID", copy=False, readonly=True, index=True)
    creator_eid = fields.Char(string="Creator's EID")

    @api.model
    def create(self, vals):
        if not vals.get("eid"):
            vals["eid"] = "New"
        res = super().create(vals)
        if res.eid == "New" and hasattr(res, "supplier_rank") and res.supplier_rank > 0:
            res.eid = res.generate_eid()
        return res

    def generate_eid(self):
        return self.env["ir.sequence"].next_by_code("enumeratorCode") or "New"
