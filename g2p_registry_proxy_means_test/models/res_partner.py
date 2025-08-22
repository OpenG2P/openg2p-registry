from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    pmt_score = fields.Float(string="PMT Score", compute="_compute_pmt_score", store=True)

    @api.depends("kind", "is_group")
    def _compute_pmt_score(self):
        for partner in self:
            score = 0.0
            pmt_params = self.env["sr.proxy.means.test.params"]

            if partner.is_group:
                pmt_params = pmt_params.search(
                    [("target", "=", "group"), ("kind", "=", partner.kind.id)], limit=1
                )
            else:
                pmt_params = pmt_params.search([("target", "=", "individual")], limit=1)

            if not pmt_params:
                partner.pmt_score = 0
                continue

            for line in pmt_params.pmt_line_ids:
                field_value = getattr(partner, line.pmt_field, 0)
                score += field_value * line.pmt_weightage

            partner.pmt_score = score

    @api.model
    def compute_existing_pmt_scores(self):
        partners = self.search([])
        for partner in partners:
            partner._compute_pmt_score()

    @api.model
    def create(self, vals):
        partner = super().create(vals)
        partner._compute_pmt_score()
        return partner

    def _get_fields_with_x_prefix(self):
        all_fields = self._fields
        return [field_name[2:] for field_name in all_fields if field_name.startswith("x_")]

    def write(self, vals):
        res = super().write(vals)
        pmt_params = self.env["sr.proxy.means.test.params"]

        if self.is_group:
            pmt_params = pmt_params.search([("target", "=", "group"), ("kind", "=", self.kind.id)], limit=1)
        else:
            pmt_params = pmt_params.search([("target", "=", "individual")], limit=1)

        fields_to_check = ["income"]

        if pmt_params:
            for line in pmt_params.pmt_line_ids:
                if line.pmt_field not in fields_to_check:
                    fields_to_check.append(line.pmt_field)

        fields_to_check.extend(self._get_fields_with_x_prefix())

        if any(field in vals for field in fields_to_check):
            for partner in self:
                partner._compute_pmt_score()
        return res
