import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class RejectWizard(models.TransientModel):
    _name = "reject.wizard"
    _description = "Reject Wizard"

    rejection_reason = fields.Text(string="Reason for Rejection", required=True)

    def confirm_rejection(self):
        active_ids = self._context.get("active_ids")
        self.ensure_one()
        record = self.env["draft.record"].browse(active_ids[0])

        record.write(
            {
                "state": "rejected",
                "rejection_reason": self.rejection_reason,
            }
        )

        record.message_post(body=f"Record rejected: {self.rejection_reason}")

        validator_group = self.env.ref("g2p_draft_publish.group_int_validator")
        validator_users = validator_group.users

        if validator_users:
            for user in validator_users:
                self.sudo().env["mail.activity"].create(
                    {
                        "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                        "res_model_id": self.sudo()
                        .env["ir.model"]
                        .search([("model", "=", "draft.record")])
                        .id,
                        "res_id": record.id,
                        "user_id": user.id,
                        "summary": "Record Rejected",
                        "note": f"Reason: {self.rejection_reason}. Please review and sumbit again.",
                    }
                )

        return {"type": "ir.actions.act_window_close"}
