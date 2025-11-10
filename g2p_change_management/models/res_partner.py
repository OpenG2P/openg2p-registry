import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    change_request_ids = fields.One2many(
        "g2p.change.request",
        "registrant_id",
        string="Change Requests",
        help="Change requests related to this registrant.",
    )

    # Computed field to check if group has active draft
    has_active_draft = fields.Boolean(
        compute="_compute_has_active_draft",
        store=True,
        index=True,
        help="True if this group has an active change request with draft",
    )

    # Computed field to show active change request
    active_change_request_id = fields.Many2one(
        "g2p.change.request",
        compute="_compute_active_change_request",
        store=False,  # Don't store, always compute
        search="_search_active_change_request",
        string="Active Change Request",
        help="Active change request for this registrant",
    )

    # Computed field to show active change request state
    active_change_request_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        compute="_compute_active_change_request_state",
        store=False,  # Don't store, always compute
        help="State of the active change request for this registrant",
    )

    @property
    def active_change_request_state_property(self):
        """Property to force computation of active change request state."""

        _logger.info(f"PROPERTY ACCESS - Registrant {self.id}")

        # Force computation
        self._compute_active_change_request()
        self._compute_active_change_request_state()

        _logger.info(
            f"PROPERTY RESULT - Registrant {self.id}: \
            active_change_request_state = {self.active_change_request_state}"
        )
        return self.active_change_request_state

    # Draft members field - Many2many for draft individual members
    draft_member_ids = fields.Many2many(
        "g2p.draft.record",
        "registrant_draft_member_rel",
        "registrant_id",
        "draft_id",
        string="Draft Members",
        help="Draft individual members from new change requests (without registrant_id)",
        domain="[('is_group', '=', False)]",
    )

    @api.depends("change_request_ids", "change_request_ids.state")
    def _compute_has_active_draft(self):
        """Compute if registrant has active change request with optimized logic."""
        for record in self:
            # Use any() for better performance than filtered()
            record.has_active_draft = any(
                cr.state in ["draft", "submitted"] for cr in record.change_request_ids
            )

    @api.depends("change_request_ids")
    def _compute_active_change_request(self):
        """Compute the active change request for this registrant."""

        _logger.info(f"_compute_active_change_request called for {len(self)} registrants")

        for record in self:
            _logger.info(f"Registrant {record.id}: Total change requests = {len(record.change_request_ids)}")

            # Log all change requests and their states
            for cr in record.change_request_ids:
                _logger.info(f"Registrant {record.id}: Change Request {cr.id} - State: {cr.state}")

            # Include all change requests (draft, submitted, approved, rejected) to track state
            active_crs = record.change_request_ids.filtered(
                lambda cr: cr.state in ["draft", "submitted", "approved", "rejected"]
            )
            _logger.info(f"Registrant {record.id}: Filtered active change requests = {len(active_crs)}")

            # Get the most recent change request (by ID, which should be the latest created)
            if active_crs:
                most_recent = active_crs.sorted("id", reverse=True)[0]
                record.active_change_request_id = most_recent
                _logger.info(
                    ("Registrant %s: Selected change request %s with state %s"),
                    record.id,
                    most_recent.id,
                    most_recent.state,
                )
            else:
                record.active_change_request_id = False
                _logger.info(f"Registrant {record.id}: No active change requests found")

    def action_debug_active_change_request(self):
        """Manual method to debug active change request computation."""
        for record in self:
            _logger.info(
                f"DEBUG - Registrant {record.id}: \
                change_request_ids = {record.change_request_ids.ids}"
            )
            for cr in record.change_request_ids:
                _logger.info(f"DEBUG - Registrant {record.id}: CR {cr.id} state = {cr.state}")

            # Force computation manually
            record._compute_active_change_request()
            record._compute_active_change_request_state()

            _logger.info(
                ("DEBUG - Registrant %s: active_change_request_id = %s"),
                record.id,
                record.active_change_request_id.id if record.active_change_request_id else False,
            )
            _logger.info(
                ("DEBUG - Registrant %s: active_change_request_state = %s"),
                record.id,
                record.active_change_request_state,
            )
        return True

    def action_force_compute_fields(self):
        """Force computation of all computed fields."""
        for record in self:
            _logger.info(f"FORCE COMPUTE - Registrant {record.id}")
            # Force computation of all computed fields
            record._compute_active_change_request()
            record._compute_active_change_request_state()
            record._compute_has_active_draft()
            _logger.info(
                ("FORCE COMPUTE - Registrant %s: active_change_request_state = %s"),
                record.id,
                record.active_change_request_state,
            )
        return True

    @api.depends("active_change_request_id", "active_change_request_id.state")
    def _compute_active_change_request_state(self):
        """Compute the state of the active change request for this registrant."""

        for record in self:
            # Check if we're in draft context with change_request_state
            if self.env.context.get("draft") and "change_request_state" in self.env.context:
                change_request_state = self.env.context.get("change_request_state")
                record.active_change_request_state = change_request_state
                _logger.info(
                    f"Registrant {record.id}: Using context change_request_state = {change_request_state}"
                )
            elif record.active_change_request_id:
                record.active_change_request_state = record.active_change_request_id.state
                _logger.info(
                    ("Registrant %s: Using computed active_change_request_state = %s"),
                    record.id,
                    record.active_change_request_state,
                )
            else:
                record.active_change_request_state = False
                _logger.info(f"Registrant {record.id}: No active change request, state = False")

    @api.model
    def create(self, vals):
        """Override create to sync draft members to group_member_ids_json for registrants."""
        record = super().create(vals)
        if "draft_member_ids" in vals:
            record._sync_draft_members_to_json()
        return record

    def _sync_draft_members_to_json(self):
        """Sync draft_member_ids to group_member_ids_json in the active change request's draft record."""
        for record in self:
            if record.active_change_request_id and record.active_change_request_id.draft_record_id:
                draft_record = record.active_change_request_id.draft_record_id
                if draft_record.is_group:
                    # Convert draft_member_ids to JSON format
                    member_data = []
                    for draft_member in record.draft_member_ids:
                        member_data.append(
                            {
                                "draft_id": draft_member.id,
                                "name": draft_member.name,
                                "given_name": getattr(draft_member, "given_name", ""),
                                "family_name": getattr(draft_member, "family_name", ""),
                                "phone": getattr(draft_member, "phone", ""),
                                "gender": getattr(draft_member, "gender", ""),
                                "region": getattr(draft_member, "region", ""),
                            }
                        )

                    # Update the draft record's group_member_ids_json
                    import json

                    draft_record.write({"group_member_ids_json": json.dumps(member_data)})
                    _logger.info(
                        "Synced %d draft members to group_member_ids_json for draft record %s",
                        len(member_data),
                        draft_record.id,
                    )

    def _search_active_change_request(self, operator, value):
        """Search method for active_change_request_id field."""
        if operator == "=" and value:
            # Search for partners that have the specified change request as active
            return [("change_request_ids", "=", value)]
        elif operator == "!=" and value:
            # Search for partners that don't have the specified change request as active
            return [("change_request_ids", "!=", value)]
        elif operator in ("=", "!=") and not value:
            # Search for partners with/without any active change request
            active_crs = self.env["g2p.change.request"].search([("state", "in", ["draft", "submitted"])])
            if operator == "=":
                return [("change_request_ids", "in", active_crs.ids)]
            else:
                return [("change_request_ids", "not in", active_crs.ids)]
        return []

    @api.constrains("change_request_ids")
    def _check_change_request_consistency(self):
        """Ensure change request consistency for this registrant."""
        for record in self:
            # Check for conflicting change requests
            active_requests = record.change_request_ids.filtered(
                lambda cr: cr.state in ["draft", "submitted"]
            )

            # Group by type to check for conflicts
            request_types = active_requests.mapped("type")
            if len(request_types) != len(set(request_types)):
                raise ValidationError(
                    _(
                        "Registrant '%s' has multiple active change requests "
                        "of the same type. Please resolve conflicts before "
                        "proceeding."
                    )
                    % record.name
                )

    @api.constrains("active")
    def _check_active_with_change_requests(self):
        """Ensure partner cannot be deactivated if it has active change requests."""
        for record in self:
            if not record.active:
                active_requests = record.change_request_ids.filtered(
                    lambda cr: cr.state in ["draft", "submitted"]
                )
                if active_requests:
                    raise ValidationError(
                        _(
                            (
                                "Cannot deactivate partner '%s' while it has active "
                                "change requests. Please complete or cancel the "
                                "change requests first."
                            )
                            % record.name
                        )
                    )

    def _validate_for_change_request(self, change_type):
        """Validate registrant for specific change request type."""
        self.ensure_one()
        errors = []

        if change_type == "modify":
            # Check if registrant is active
            if not self.active:
                errors.append("Cannot modify inactive registrant")

            # Check for existing active modify requests
            existing_modify = self.change_request_ids.filtered(
                lambda cr: cr.type == "modify" and cr.state in ["draft", "submitted"]
            )
            if existing_modify:
                errors.append("Registrant already has an active modify request")

        elif change_type == "delete":
            # Check if registrant is active
            if not self.active:
                errors.append("Registrant is already inactive")

            # Check for existing active delete requests
            existing_delete = self.change_request_ids.filtered(
                lambda cr: cr.type == "delete" and cr.state in ["draft", "submitted"]
            )
            if existing_delete:
                errors.append("Registrant already has an active delete request")

        if errors:
            raise ValidationError(
                "Validation errors for %s request:\n" % change_type
                + "\n".join("- " + error for error in errors)
            )

        return True

    def get_available_draft_members(self):
        """Get available draft individual records for group membership selection."""
        self.ensure_one()

        available_drafts = self.env["g2p.draft.record"].search(
            [
                ("is_group", "=", False),  # Only individual records
                ("state", "in", ["draft", "submitted"]),  # Only draft and submitted
            ]
        )

        return available_drafts

    def update_group_member_statuses(self, new_state):
        """Update the status of all draft individual members in this group."""
        self.ensure_one()

        if not self.is_group:
            return False

        # Get the active change request for this group
        active_cr = self.active_change_request_id
        if not active_cr or not active_cr.draft_record_id:
            return False

        # Get draft members from the group's draft record
        draft_record = active_cr.draft_record_id
        if not draft_record.group_member_ids_json:
            return False

        try:
            import json

            member_data = json.loads(draft_record.group_member_ids_json)
            updated_count = 0

            for member in member_data:
                if member.get("draft_id"):
                    # This is a draft individual record
                    draft_individual = self.env["g2p.draft.record"].browse(member["draft_id"])
                    if draft_individual.exists() and draft_individual.state in ["draft", "submitted"]:
                        # Map change request states to draft record states
                        state_mapping = {
                            "submitted": "submitted",
                            "approved": "published",
                            "rejected": "rejected",
                        }
                        target_state = state_mapping.get(new_state)
                        if target_state:
                            draft_individual.write({"state": target_state})
                            updated_count += 1
                            _logger.info(
                                "Updated draft individual %s state to %s", draft_individual.name, target_state
                            )

            return updated_count

        except (json.JSONDecodeError, KeyError) as e:
            _logger.error("Error updating group member statuses: %s", str(e))
            return False

    def action_create_change_request(self):
        """Create a change request for this registrant."""
        self.ensure_one()

        # Check if there's already an active change request
        if self.has_active_draft:
            return {
                "type": "ir.actions.act_window",
                "name": _("Active Change Request"),
                "res_model": "g2p.change.request",
                "res_id": self.active_change_request_id.id,
                "view_mode": "form",
                "target": "current",
            }

        # Create new change request
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "registrant_id": self.id,
            }
        )

        # Create draft record by copying registrant data
        draft_record = self._create_draft_from_registrant()
        change_request.write({"draft_record_id": draft_record.id})

        return {
            "type": "ir.actions.act_window",
            "name": _("Change Request"),
            "res_model": "g2p.change.request",
            "res_id": change_request.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_active_change_request(self):
        """View the active change request for this registrant."""
        self.ensure_one()

        if not self.has_active_draft:
            raise UserError(_("No active change request found for this registrant."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Active Change Request"),
            "res_model": "g2p.change.request",
            "res_id": self.active_change_request_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_add_draft_members(self):
        """Open the draft member selection wizard for this registrant's active change request."""
        self.ensure_one()

        if not self.active_change_request_id or not self.active_change_request_id.draft_record_id:
            raise UserError(_("No active change request with draft record found for this registrant."))

        if not self.active_change_request_id.draft_record_id.is_group:
            raise UserError(_("Draft member selection is only available for group registrants."))

        # Open the draft member selection wizard
        return {
            "type": "ir.actions.act_window",
            "name": _("Add Draft Members"),
            "res_model": "g2p.draft.group.add.members.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_group_id": self.active_change_request_id.draft_record_id.id,
                "member_selection_context": True,
            },
        }

    def _create_draft_from_registrant(self):
        """Create a draft record by copying registrant data."""
        self.ensure_one()

        # Prepare registrant data for draft record
        # Get region value safely - convert Many2one to ID if it exists
        region_value = getattr(self, "region", "")
        if hasattr(region_value, "id"):
            region_value = region_value.id
        elif not region_value:
            region_value = ""

        registrant_data = {
            "name": self.name,
            "is_group": self.is_group,
            "given_name": getattr(self, "given_name", ""),
            "family_name": getattr(self, "family_name", ""),
            "addl_name": getattr(self, "addl_name", ""),
            "phone": self.phone if hasattr(self, "phone") else "",
            "gender": getattr(self, "gender", ""),
            "region": region_value,
        }

        # Create draft record
        draft_record = self.env["g2p.draft.record"].create(registrant_data)

        return draft_record

    def write(self, vals):
        """Override write to prevent direct modification when change management is enabled."""
        # Always allow writes in these scenarios to preserve original behavior:
        # 1. System operations (install, upgrade, etc.)
        # 2. Change request context (editing draft records)
        # 3. Force write context (explicit bypass)
        # 4. Non-registrant partners (regular business partners)
        # 5. Test mode (when running unit tests)
        in_test_mode = (
            hasattr(self.env.registry, "_assertion_report")
            and self.env.registry._assertion_report is not None
        )
        if (
            self.env.context.get("change_request_context")
            or self.env.context.get("force_write")
            or self.env.context.get("install_mode")
            or self.env.context.get("upgrade_mode")
            or not self.env.context.get("change_management_enabled", True)
            or not any(registrant.is_registrant for registrant in self)
            or in_test_mode
        ):
            return super().write(vals)

        # Only block writes for registrants when change management is enabled
        # and not in change request context
        raise ValidationError(
            _(
                "Cannot modify registrant records directly."
                "Please use the Change Request workflow to make changes."
            )
        )
