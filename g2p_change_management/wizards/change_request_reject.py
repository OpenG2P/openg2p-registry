import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


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

        if self.change_request_id.draft_record_id and self.change_request_id.draft_record_id.is_group:
            updated_count = self.change_request_id._update_group_member_statuses("rejected")
            if updated_count > 0:
                self.change_request_id.message_post(
                    body=_("Updated status of %(count)s draft individual members to 'rejected'.")
                    % {"count": updated_count}
                )

        # Notify requester and close activities
        self.change_request_id._send_approval_result_notification("rejected")
        self.change_request_id._close_related_activities()

        _logger.info(
            "Change request %s rejected by %s. Reason: %s",
            self.change_request_id.name,
            self.env.user.name,
            self.rejection_reason,
        )

        return {"type": "ir.actions.act_window_close"}
