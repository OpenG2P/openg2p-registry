import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DraftRecord(models.Model):
    _inherit = "draft.record"

    # Add missing fields that are expected by the view
    disabled = fields.Datetime("Date Disabled")
    disabled_reason = fields.Text("Reason for Disabling")
    disabled_by = fields.Many2one("res.users")

    # Draft members field - Many2many relationship for draft individual members
    draft_member_ids = fields.Many2many(
        "draft.record",
        "draft_group_member_rel",
        "group_id",
        "member_id",
        string="Draft Members",
        help="Draft individual members of this group",
        domain="[('is_group', '=', False)]",
    )

    def _return_wizard_with_context(self, view_id):
        """Override to filter out draft_member_ids from partner_data before processing."""
        # Get the partner_data and filter out draft_member_ids
        if self.partner_data:
            try:
                import json

                json_data = json.loads(self.partner_data)
                # Remove draft_member_ids if it exists
                if "draft_member_ids" in json_data:
                    del json_data["draft_member_ids"]
                # Update the partner_data with filtered data
                self.partner_data = json.dumps(json_data)
            except (json.JSONDecodeError, KeyError) as err:
                _logger.warning(
                    "Failed to filter draft_member_ids from partner_data JSON for draft record %s: %s",
                    self.id,
                    err,
                )  # Continue with original data

        # Call the parent method
        return super()._return_wizard_with_context(view_id)
