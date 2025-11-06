import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BulkOperationsWizard(models.TransientModel):
    _name = "g2p.change.request.bulk.wizard"
    _description = "Bulk Operations Wizard for Change Requests"

    operation_type = fields.Selection(
        [
            ("approve", "Approve"),
            ("reject", "Reject"),
            ("submit", "Submit"),
            ("cancel", "Cancel"),
            ("assign", "Assign"),
        ],
        required=True,
    )

    change_request_ids = fields.Many2many("g2p.change.request", string="Change Requests", required=True)

    reason = fields.Text(string="Reason/Comment", help="Provide a reason or comment for this bulk operation")

    assign_to_user_id = fields.Many2one(
        "res.users", string="Assign To", help="Select user to assign the change requests to"
    )

    operation_summary = fields.Text(readonly=True, compute="_compute_operation_summary")

    @api.depends("change_request_ids", "operation_type")
    def _compute_operation_summary(self):
        """Compute summary of the bulk operation"""
        for wizard in self:
            if wizard.change_request_ids:
                count = len(wizard.change_request_ids)
                operation = wizard.operation_type.title()
                wizard.operation_summary = f"This will {operation.lower()} {count} change request(s)."
            else:
                wizard.operation_summary = ""

    @api.model
    def default_get(self, fields_list):
        """Set default values from context"""
        res = super().default_get(fields_list)

        # Get change request IDs from context
        if "active_ids" in self.env.context:
            res["change_request_ids"] = [(6, 0, self.env.context["active_ids"])]

        # Get operation type from context
        if "operation_type" in self.env.context:
            res["operation_type"] = self.env.context["operation_type"]

        return res

    def action_confirm(self):
        """Execute the bulk operation"""
        self.ensure_one()

        if not self.change_request_ids:
            raise UserError(_("No change requests selected for bulk operation."))

        # Validate permissions
        if not self._validate_permissions():
            raise UserError(_("You don't have permission to perform this bulk operation."))

        # Execute the operation based on type
        try:
            if self.operation_type == "approve":
                self._bulk_approve()
            elif self.operation_type == "reject":
                self._bulk_reject()
            elif self.operation_type == "submit":
                self._bulk_submit()
            elif self.operation_type == "cancel":
                self._bulk_cancel()
            elif self.operation_type == "assign":
                self._bulk_assign()

            # Show success message
            count = len(self.change_request_ids)
            operation = self.operation_type.title()
            message = _(
                "Successfully %(op)s %(count)d change request(s).",
                op=operation.lower() + "d",
                count=count,
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Bulk Operation Completed"),
                    "message": message,
                    "type": "success",
                    "sticky": False,
                },
            }

        except Exception as err:
            _logger.error("Bulk operation failed: %s", str(err))
            raise UserError(_("Bulk operation failed: %s") % str(err)) from err

    def _validate_permissions(self):
        """Validate user permissions for bulk operations"""
        user = self.env.user

        if self.operation_type in ["approve", "reject"]:
            return user.has_group("g2p_change_management.group_change_management_approver")
        elif self.operation_type in ["submit", "cancel"]:
            return user.has_group("g2p_change_management.group_change_management_user")
        elif self.operation_type == "assign":
            return user.has_group("g2p_change_management.group_change_management_approver")

        return False

    def _bulk_approve(self):
        """Bulk approve change requests"""
        for change_request in self.change_request_ids:
            if change_request.state == "submitted":
                change_request.with_context(bulk_operation=True, bulk_reason=self.reason).action_approve()
            else:
                _logger.warning(
                    "Cannot approve change request %s: invalid state %s",
                    change_request.name,
                    change_request.state,
                )

    def _bulk_reject(self):
        """Bulk reject change requests"""
        for change_request in self.change_request_ids:
            if change_request.state == "submitted":
                change_request.with_context(bulk_operation=True, bulk_reason=self.reason).action_reject()
            else:
                _logger.warning(
                    "Cannot reject change request %s: invalid state %s",
                    change_request.name,
                    change_request.state,
                )

    def _bulk_submit(self):
        """Bulk submit change requests"""
        for change_request in self.change_request_ids:
            if change_request.state == "draft":
                change_request.with_context(bulk_operation=True, bulk_reason=self.reason).action_submit()
            else:
                _logger.warning(
                    "Cannot submit change request %s: invalid state %s",
                    change_request.name,
                    change_request.state,
                )

    def _bulk_cancel(self):
        """Bulk cancel change requests"""
        for change_request in self.change_request_ids:
            if change_request.state in ["draft", "submitted"]:
                change_request.with_context(bulk_operation=True, bulk_reason=self.reason).write(
                    {"state": "cancelled"}
                )
            else:
                _logger.warning(
                    "Cannot cancel change request %s: invalid state %s",
                    change_request.name,
                    change_request.state,
                )

    def _bulk_assign(self):
        """Bulk assign change requests to user"""
        if not self.assign_to_user_id:
            raise UserError(_("Please select a user to assign the change requests to."))

        for change_request in self.change_request_ids:
            change_request.with_context(bulk_operation=True, bulk_reason=self.reason).write(
                {"requester_id": self.assign_to_user_id.id}
            )
