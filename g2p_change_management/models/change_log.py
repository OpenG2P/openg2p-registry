import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ChangeLog(models.Model):
    _name = "g2p.change.log"
    _description = "Change Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "change_date desc"
    _rec_name = "change_summary"

    change_request_id = fields.Many2one(
        "g2p.change.request",
        string="Change Request",
        required=True,
        ondelete="cascade",
        index=True,
        help="The change request that triggered this log entry.",
    )

    registrant_id = fields.Many2one(
        "res.partner",
        string="Registrant",
        required=True,
        index=True,
        help="The registrant record that was affected by the change.",
    )

    change_type = fields.Selection(
        selection=[
            ("create", "Create"),
            ("modify", "Modify"),
            ("delete", "Delete"),
        ],
        required=True,
        help="Type of change that was made.",
    )

    old_values = fields.Json(
        help="JSON representation of the old values before the change.",
    )

    new_values = fields.Json(
        help="JSON representation of the new values after the change.",
    )

    old_values_formatted = fields.Text(
        compute="_compute_formatted_values",
        help="Formatted display of old values as JSON string.",
    )

    new_values_formatted = fields.Text(
        string="New Values (Formatted)",
        compute="_compute_formatted_values",
        help="Formatted display of new values as JSON string.",
    )

    changed_by = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        help="User who approved and implemented the change.",
    )

    change_date = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        help="Date and time when the change was implemented.",
    )

    change_summary = fields.Char(
        required=True,
        help="Brief summary of what was changed.",
    )

    is_group = fields.Boolean(
        related="registrant_id.is_group",
        store=True,
        readonly=True,
        help="Indicates if the change was for a group record.",
    )

    registrant_name = fields.Char(
        string="Registrant Name",
        related="registrant_id.name",
        store=True,
        help="Name of the affected registrant.",
    )

    change_request_name = fields.Char(
        string="Change Request Name",
        related="change_request_id.name",
        store=True,
        help="Name of the change request.",
    )

    @api.model
    def create(self, vals):
        """Override create to prevent manual creation of change log records."""
        # Only allow creation through the create_change_log method
        if not self.env.context.get("allow_change_log_creation"):
            raise UserError(
                _(
                    "Change log records cannot be created manually. "
                    "They are automatically generated when change requests are approved."
                )
            )
        return super().create(vals)

    def write(self, vals):
        """Override write to prevent modification of change log records."""
        # pylint: disable=method-required-super
        raise UserError(_("Change log records cannot be modified. They are immutable audit records."))

    def unlink(self):
        """Override unlink to prevent deletion of change log records."""
        # pylint: disable=method-required-super
        raise UserError(_("Change log records cannot be deleted. They are permanent audit records."))

    @api.depends("old_values", "new_values")
    def _compute_formatted_values(self):
        """Format JSON values for better display."""
        for record in self:
            if record.old_values:
                record.old_values_formatted = json.dumps(record.old_values, indent=2, ensure_ascii=False)
            else:
                record.old_values_formatted = "No previous values"

            if record.new_values:
                record.new_values_formatted = json.dumps(record.new_values, indent=2, ensure_ascii=False)
            else:
                record.new_values_formatted = "No new values"

    @api.model
    def create_change_log(self, change_request, registrant, change_type, old_values=None, new_values=None):
        """
        Create a change log entry for a change request.

        Args:
            change_request: change.request record
            registrant: res.partner record that was affected
            change_type: 'create', 'modify', or 'delete'
            old_values: dict of old values (for modify/delete)
            new_values: dict of new values (for create/modify)
        """
        try:
            # Generate change summary
            change_summary = self._generate_change_summary(change_type, registrant, old_values, new_values)

            # Create the log entry
            log_data = {
                "change_request_id": change_request.id,
                "registrant_id": registrant.id,
                "change_type": change_type,
                "changed_by": self.env.user.id,
                "change_date": fields.Datetime.now(),
                "change_summary": change_summary,
                "is_group": getattr(registrant, "is_group", False),
            }

            # Add JSON values if provided (JSON fields accept dicts directly)
            if old_values:
                log_data["old_values"] = old_values
            if new_values:
                log_data["new_values"] = new_values

            change_log = self.with_context(allow_change_log_creation=True).create(log_data)

            _logger.info(
                "Created change log entry %s for change request %s, registrant %s",
                change_log.id,
                change_request.name,
                registrant.name,
            )

            return change_log

        except Exception as e:
            _logger.error(
                "Failed to create change log for change request %s: %s", change_request.name, str(e)
            )
            # Don't raise the error to avoid breaking the main workflow
            return False

    def _generate_change_summary(self, change_type, registrant, old_values=None, new_values=None):
        """Generate a human-readable summary of the change."""
        registrant_name = registrant.name or "Unknown Registrant"

        if change_type == "create":
            return f"Created new registrant: {registrant_name}"
        elif change_type == "modify":
            # Try to identify what fields changed
            changed_fields = []
            if old_values and new_values:
                for field, new_value in new_values.items():
                    old_value = old_values.get(field)
                    if old_value != new_value:
                        changed_fields.append(field)

            if changed_fields:
                return f"Modified registrant {registrant_name}: changed {', '.join(changed_fields[:3])}"
            else:
                return f"Modified registrant: {registrant_name}"
        elif change_type == "delete":
            return f"Deactivated registrant: {registrant_name}"
        else:
            return f"Unknown change type for registrant: {registrant_name}"

    @api.model
    def get_registrant_change_history(self, registrant_id):
        """Get change history for a specific registrant."""
        return self.search([("registrant_id", "=", registrant_id)], order="change_date desc")

    @api.model
    def get_change_request_logs(self, change_request_id):
        """Get all logs for a specific change request."""
        return self.search([("change_request_id", "=", change_request_id)], order="change_date desc")

    def action_view_change_request(self):
        """Open the related change request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Change Request",
            "res_model": "g2p.change.request",
            "res_id": self.change_request_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_registrant(self):
        self.ensure_one()
        if not self.registrant_id:
            raise UserError(_("No registrant to open."))
        if self.is_group:
            view_id = self.env.ref("g2p_registry_group.view_groups_form").id
        else:
            view_id = self.env.ref("g2p_registry_individual.view_individuals_form").id
        return {
            "type": "ir.actions.act_window",
            "name": "Registrant",
            "res_model": "res.partner",
            "res_id": self.registrant_id.id,
            "view_mode": "form",
            "view_id": view_id,
            "target": "current",
        }
