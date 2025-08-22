from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SRProxyMeanTestParams(models.Model):
    _name = "sr.proxy.means.test.params"
    _description = "Proxy Means Test Params"
    _rec_name = "pmt_name"

    pmt_name = fields.Char(
        string="PMT Name",
    )
    target = fields.Selection(
        [("individual", "Individual"), ("group", "Group")],
    )
    kind = fields.Many2one(
        "g2p.group.kind",
    )

    pmt_line_ids = fields.One2many("sr.proxy.means.test.line", "pmt_id", string="Proxy Means Test Lines")

    target_name = fields.Boolean(default=True)

    @api.onchange("target")
    def _onchange_target(self):
        if self.target == "group":
            self.write({"target_name": False})
        else:
            self.write({"target_name": True})

    @api.constrains("target", "kind")
    def _check_unique_pmt(self):
        for rec in self:
            existing_pmt = self.search_count(
                [("target", "=", rec.target), ("kind", "=", rec.kind.id), ("id", "!=", rec.id)]
            )

            if existing_pmt > 0:
                raise ValidationError(_("A Proxy Means Test for this kind and target already exists."))

    @api.model
    def create(self, vals):
        if "target" in vals and "kind" in vals:
            existing_pmt = self.search_count([("target", "=", vals["target"]), ("kind", "=", vals["kind"])])
            if existing_pmt > 0:
                raise ValidationError(_("A Proxy Means Test for this kind and target already exists."))

        rec = super().create(vals)
        rec.compute_related_partners_pmt_score()
        return rec

    def write(self, vals):
        for rec in self:
            if "target" in vals and vals["target"] != rec.target:
                existing_pmt = self.search_count(
                    [("target", "=", vals["target"]), ("kind", "=", rec.kind.id), ("id", "!=", rec.id)]
                )
                if existing_pmt > 0:
                    raise ValidationError(_("A Proxy Means Test for this kind and target already exists."))

            if "kind" in vals and vals["kind"] != rec.kind.id:
                existing_pmt = self.search_count(
                    [("target", "=", rec.target), ("kind", "=", vals["kind"]), ("id", "!=", rec.id)]
                )
                if existing_pmt > 0:
                    raise ValidationError(_("A Proxy Means Test for this kind and target already exists."))

        rec = super().write(vals)
        for record in self:
            record.compute_related_partners_pmt_score()
        return rec

    def unlink(self):
        for rec in self:
            partners = self.env["res.partner"].search([("kind", "=", rec.kind.id)])
            for partner in partners:
                partner.pmt_score = 0

        rec.pmt_line_ids.unlink()
        return super().unlink()

    def compute_related_partners_pmt_score(self):
        if (
            not self.target
            or not self.pmt_name
            or not self.pmt_line_ids
            or (self.target == "group" and not self.kind)
        ):
            return
        partners = self.env["res.partner"].search([("kind", "=", self.kind.id)])
        for partner in partners:
            partner._compute_pmt_score()
