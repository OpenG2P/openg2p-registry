from odoo import api, fields, models


class OdkInstanceId(models.Model):
    _name = "odk.instance.id"
    _description = "ODK Instance ID"

    instance_id = fields.Char(string="Instance ID", required=True, index=True)
    status = fields.Selection(
        [("pending", "Pending"), ("processing", "Processing"), ("done", "Done"), ("failed", "Failed")],
        default="pending",
        required=True,
    )
    odk_import_id = fields.Many2one("odk.import", string="ODK Import", required=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        # Additional logic if needed
        return record

    def set_status(self, status):
        self.status = status
