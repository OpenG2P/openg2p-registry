from odoo import _, fields, models


class ChangeRequestRejectWizard(models.TransientModel):
    _name = "g2p.change.request.reject.wizard"
    _description = "Reject Change Request Wizard"

    change_request_id = fields.Many2one(
        "g2p.change.request",
        string="Change Request",
        required=True,
        default=lambda self: self.env.context.get("default_change_request_id"),
    )

    rejection_reason = fields.Text(
        required=True,
        help="Please provide a reason for rejecting this change request.",
    )

    def action_confirm_rejection(self):
        """Confirm the rejection of the change request."""
        self.ensure_one()

        self.change_request_id.write(
            {
                "state": "rejected",
                "rejection_reason": self.rejection_reason,
                "approver_id": self.env.user.id,
            }
        )

        self.change_request_id.message_post(
            body=_("Change request rejected. Reason: %s") % self.rejection_reason
        )

        return {"type": "ir.actions.act_window_close"}
