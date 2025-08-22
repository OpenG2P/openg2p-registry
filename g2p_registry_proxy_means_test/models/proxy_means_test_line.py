from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SRProxyMeanTestLine(models.Model):
    _name = "sr.proxy.means.test.line"
    _description = "Proxy Means Test Line"

    pmt_id = fields.Many2one("sr.proxy.means.test.params", string="Proxy Means Test")
    pmt_field = fields.Selection(selection="get_fields_label", string="Field")
    pmt_weightage = fields.Float(string="Weightage")

    @api.constrains("pmt_id", "pmt_field")
    def _check_unique_field_weightage(self):
        for line in self:
            duplicate = self.search_count(
                [("pmt_id", "=", line.pmt_id.id), ("pmt_field", "=", line.pmt_field), ("id", "!=", line.id)]
            )
            if duplicate:
                raise ValidationError(_("The combination of PMT field and weightage already exist."))

    def get_fields_label(self):
        reg_info = self.env["res.partner"]
        ir_model_obj = self.env["ir.model.fields"]
        excluded_fields = {
            "pmt_score",
            "message_needaction_counter",
            "message_has_error_counter",
            "message_attachment_count",
            "message_bounce",
            "active_lang_count",
            "partner_latitude",
            "partner_longitude",
            "color",
            "id",
            "meeting_count",
            "employees_count",
            "partner_gid",
            "certifications_count",
            "certifications_company_count",
            "event_count",
            "payment_token_count",
            "days_sales_outstanding",
            "journal_item_count",
            "bank_account_count",
            "supplier_rank",
            "customer_rank",
            "duplicated_bank_account_partners_count",
            "task_count",
            "z_ind_grp_num_individuals",
            "program_membership_count",
            "entitlements_count",
            "cycles_count",
            "inkind_entitlements_count",
            "credit_limit",
        }

        choice = []
        for field in reg_info._fields.items():
            ir_model_field = ir_model_obj.search([("model", "=", "res.partner"), ("name", "=", field[0])])
            field_type = ir_model_field.ttype
            if field_type in ["integer", "float"] and field[0] not in excluded_fields:
                choice.append((field[0], field[0]))
        return choice

    def write(self, vals):
        res = super().write(vals)
        for line in self:
            line.pmt_id.compute_related_partners_pmt_score()
        return res
