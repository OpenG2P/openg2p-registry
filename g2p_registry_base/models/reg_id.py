# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


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

    def name_get(self):
        res = super(G2PRegistrantID, self).name_get()
        for rec in self:
            name = ""
            if rec.partner_id:
                name = rec.partner_id.name
            res.append((rec.id, name))
        return res

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        if name:
            args = [("partner_id", operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)


class G2PIDType(models.Model):
    _name = "g2p.id.type"
    _description = "ID Type"
    _order = "id desc"

    name = fields.Char()
