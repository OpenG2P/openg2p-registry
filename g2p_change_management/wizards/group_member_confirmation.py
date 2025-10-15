import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GroupMemberConfirmationWizard(models.TransientModel):
    _name = "group.member.confirmation.wizard"
    _description = "Group Member Status Update Confirmation"

    change_request_id = fields.Many2one(
        "change.request",
        string="Change Request",
        required=True,
        readonly=True,
    )

    action_type = fields.Selection(
        selection=[
            ("submit", "Submit"),
            ("approve", "Approve"),
            ("reject", "Reject"),
        ],
        required=True,
        readonly=True,
    )

    member_count = fields.Integer(
        string="Number of Members to Update",
        readonly=True,
    )

    member_names = fields.Text(
        readonly=True,
        help="List of draft individual members that will be updated",
    )

    confirmation_message = fields.Text(
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values for the wizard."""
        res = super().default_get(fields_list)

        if self.env.context.get("active_id"):
            change_request = self.env["change.request"].browse(self.env.context.get("active_id"))
            action_type = self.env.context.get("action_type", "submit")

            if change_request and change_request.draft_record_id and change_request.draft_record_id.is_group:
                # Get member information
                member_info = self._get_member_info(change_request)

                res.update(
                    {
                        "change_request_id": change_request.id,
                        "action_type": action_type,
                        "member_count": member_info.get("count", 0),
                        "member_names": member_info.get("names", ""),
                        "confirmation_message": self._get_confirmation_message(
                            action_type, member_info.get("count", 0)
                        ),
                    }
                )

        return res

    def _get_member_info(self, change_request):
        """Get information about draft members in the group."""
        draft_record = change_request.draft_record_id
        if not draft_record.group_member_ids_json:
            return {"count": 0, "names": ""}

        try:
            import json

            member_data = json.loads(draft_record.group_member_ids_json)
            draft_members = []

            for member in member_data:
                if member.get("draft_id"):
                    draft_individual = self.env["draft.record"].browse(member["draft_id"])
                    if draft_individual.exists() and draft_individual.state in ["draft", "submitted"]:
                        draft_members.append(draft_individual.name)

            return {
                "count": len(draft_members),
                "names": "\n".join(draft_members) if draft_members else "No draft members found",
            }

        except (json.JSONDecodeError, KeyError):
            return {"count": 0, "names": "Error reading member data"}

    def _get_confirmation_message(self, action_type, member_count):
        """Generate confirmation message based on action type."""
        if member_count == 0:
            return "No draft individual members found to update."

        state_mapping = {
            "submit": "submitted",
            "approve": "published",
            "reject": "rejected",
        }
        target_state = state_mapping.get(action_type, action_type)

        return _(
            "This action will update the status of %(count)d draft individual member(s) "
            "to '%(state)s'.\n\nDo you want to proceed?",
            count=member_count,
            state=target_state,
        )

    def action_confirm(self):
        """Confirm the group member status update."""
        self.ensure_one()

        if self.member_count == 0:
            raise UserError(_("No draft members found to update."))

        # Call the original action method with confirmation context
        action_method = getattr(self.change_request_id, f"action_{self.action_type}", None)
        if action_method:
            # Add confirmation context to prevent showing the wizard again
            self.change_request_id = self.change_request_id.with_context(group_member_confirmed=True)
            return action_method()
        else:
            raise UserError(_("Action method 'action_%s' not found.") % self.action_type)

    def action_cancel(self):
        """Cancel the group member status update."""
        return {"type": "ir.actions.act_window_close"}
