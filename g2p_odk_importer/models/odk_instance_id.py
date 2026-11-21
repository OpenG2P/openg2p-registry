from odoo import _, fields, models, tools


class OdkInstanceId(models.Model):
    _name = "odk.instance.id"
    _description = "ODK Instance ID"
    _order = "create_date desc, id desc"
    _rec_name = "instance_id"

    instance_id = fields.Char(string="Instance ID", required=True, index=True)
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("queued", "Queued"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("partial", "Partial"),
            ("failed", "Failed"),
        ],
        default="pending",
        required=True,
        index=True,
    )
    odk_import_id = fields.Many2one(
        "odk.import",
        string="ODK Import",
        required=True,
        ondelete="cascade",
        index=True,
    )
    error_message = fields.Text(readonly=True)

    _sql_constraints = [
        (
            "odk_instance_id_unique",
            "unique(instance_id)",
            "This ODK instance ID has already been imported. "
            "Delete the existing entry to allow re-import.",
        ),
    ]

    def init(self):
        # Speeds pending-claim: WHERE odk_import_id = %s AND status = 'pending'
        tools.create_index(
            self._cr,
            "odk_instance_id_import_status_idx",
            self._table,
            ["odk_import_id", "status"],
        )

    def set_status(self, status, error_message=None):
        vals = {"status": status}
        if error_message is not None:
            vals["error_message"] = error_message
        elif status == "done":
            # Clear prior failure/partial messages only on clean success.
            vals["error_message"] = False
        self.write(vals)

    def action_reset_to_pending(self):
        """Reset selected instances to pending so they can be queued again."""
        to_reset = self.filtered(lambda rec: rec.status != "pending")
        to_reset.write({"status": "pending", "error_message": False})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": _("%s instance(s) reset to pending.") % len(to_reset),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
