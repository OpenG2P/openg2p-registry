import json
import logging
from datetime import date, datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ChangeRequest(models.Model):
    _name = "g2p.change.request"
    _description = "Change Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name = "name"

    name = fields.Char(
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: "New",
    )

    type = fields.Selection(
        selection=[
            ("create", "Create"),
            ("modify", "Modify"),
            ("delete", "Delete"),
        ],
        required=True,
        default="create",
        tracking=True,
    )

    is_group = fields.Boolean(
        default=False,
        tracking=True,
        help="Indicates if this change request is for a group (True) or individual (False).",
    )

    group_kind_id = fields.Many2one(
        "g2p.group.kind",
        string="Group Kind",
        tracking=True,
        help="Type of group for group change requests.",
    )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
        copy=False,
        index=True,
        help="Current state of the change request.",
    )

    registrant_id = fields.Many2one(
        "res.partner",
        string="Registrant",
        tracking=True,
        index=True,
        help="The registrant record this change request relates to. Empty for create requests.",
    )

    draft_record_id = fields.Many2one(
        "g2p.draft.record",
        string="Draft Record",
        tracking=True,
        help="The draft record containing the proposed changes.",
    )

    registrant_data = fields.Json(
        string="Registrant Data (JSON)",
        help="JSON data for registrant form wizard",
    )

    requester_id = fields.Many2one(
        "res.users",
        string="Requester",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
        help="User who created this change request.",
    )

    approver_id = fields.Many2one(
        "res.users",
        string="Approver",
        tracking=True,
        help="User who approved or rejected this change request.",
    )

    rejection_reason = fields.Text(
        tracking=True,
        help="Reason for rejection if the change request was rejected.",
    )

    change_reason = fields.Selection(
        selection="_get_change_reason_selection",
        tracking=True,
        help="Reason for the change request. Configure reasons in Configuration > Change Reasons.",
        copy=False,
    )

    change_source = fields.Selection(
        selection=[
            ("non_form_based", "Non-form based"),
            ("form_based", "Form based"),
        ],
        tracking=True,
        copy=False,
    )

    supporting_documents_ids = fields.One2many(
        "storage.file",
        "change_request_id",
        string="Supporting Documents",
        help="Files or documents submitted in support of this change request.",
    )
    tags_ids = fields.Many2many("g2p.document.tag")

    @api.model
    def _get_change_reason_selection(self):
        reasons = self.env["g2p.change.request.reason"].search([("active", "=", True)], order="name")
        selection_list = [(str(reason.id), reason.name) for reason in reasons]
        if selection_list:
            return [("", "")] + selection_list
        return [("", "No reasons configured")]

    # Computed fields
    registrant_name = fields.Char(
        compute="_compute_registrant_name",
        store=True,
        index=True,
        help="Name of the associated registrant",
    )

    # Draft record computed fields for display
    draft_name = fields.Char(
        compute="_compute_draft_fields",
        store=True,
    )

    draft_is_group = fields.Boolean(
        compute="_compute_draft_fields",
        store=True,
    )

    draft_given_name = fields.Char(
        compute="_compute_draft_fields",
        store=True,
    )

    draft_family_name = fields.Char(
        compute="_compute_draft_fields",
        store=True,
    )

    draft_phone = fields.Char(
        compute="_compute_draft_fields",
        store=True,
    )

    draft_region = fields.Char(
        compute="_compute_draft_fields",
        store=True,
    )

    # Registrant computed fields for display
    registrant_given_name = fields.Char(
        compute="_compute_registrant_fields",
        store=True,
    )

    registrant_family_name = fields.Char(
        compute="_compute_registrant_fields",
        store=True,
    )

    registrant_phone = fields.Char(
        compute="_compute_registrant_fields",
        store=True,
    )

    registrant_region = fields.Char(
        compute="_compute_registrant_fields",
        store=True,
    )

    # Validation fields
    validation_summary = fields.Text(
        compute="_compute_validation_summary",
        store=True,
        help="Summary of validation status and any errors found.",
    )

    has_validation_errors = fields.Boolean(
        compute="_compute_validation_summary",
        store=True,
        help="Indicates if there are any validation errors.",
    )

    can_submit = fields.Boolean(
        compute="_compute_can_submit",
        store=True,
        help="Indicates if the change request can be submitted.",
    )

    can_approve = fields.Boolean(
        compute="_compute_can_approve",
        store=True,
        help="Indicates if the change request can be approved.",
    )

    can_reject = fields.Boolean(
        compute="_compute_can_reject",
        store=True,
        help="Indicates if the change request can be rejected.",
    )

    @api.model
    def create(self, vals):
        """Override create to generate meaningful name and create draft record."""
        # Set default values
        if "type" not in vals:
            vals["type"] = "create"
        if "state" not in vals:
            vals["state"] = "draft"
        if "requester_id" not in vals:
            vals["requester_id"] = self.env.user.id

        # Create the change request first to get the ID
        change_request = super().create(vals)

        # Generate a meaningful name based on registrant name and unique_id
        if change_request.name == "New":
            # For new change requests, we'll update the name after the draft record is created
            change_request.name = f"CR #{change_request.id}"

        # Create draft record after change request is created
        draft_record = change_request._create_draft_record_for_different_type_cr()
        if draft_record:
            change_request.write({"draft_record_id": draft_record.id})

        # Update the change request name based on the draft record
        change_request._update_change_request_name()

        return change_request

    def _update_change_request_name(self):
        """Update the change request name based on registrant name and unique_id."""
        self.ensure_one()

        # Get the registrant name and unique_id for display
        registrant_name = ""
        unique_id = ""

        # Prioritize draft record name for create requests
        if self.type == "create" and self.draft_record_id:
            registrant_name = self.draft_record_id.name
            # For draft records, we might not have unique_id yet, so use name
        elif self.registrant_id:
            registrant_name = self.registrant_id.name
            unique_id = getattr(self.registrant_id, "unique_id", "")
        elif self.draft_record_id:
            registrant_name = self.draft_record_id.name
            # For draft records, we might not have unique_id yet, so use name

        # Create the name: Registrant Name (Unique ID) - CR #ID
        if registrant_name and unique_id:
            self.name = f"{registrant_name} ({unique_id}) - CR #{self.id}"
        elif registrant_name:
            self.name = f"{registrant_name} - CR #{self.id}"
        else:
            self.name = f"CR #{self.id}"

    def update_name_from_registrant(self):
        """Update change request name when registrant is saved/updated."""
        for record in self:
            record._update_change_request_name()

    @api.depends("registrant_id", "registrant_id.name")
    def _compute_registrant_name(self):
        """Compute registrant name for display purposes with optimized dependencies."""
        for record in self:
            record.registrant_name = record.registrant_id.name if record.registrant_id else ""

    @api.depends(
        "draft_record_id",
        "draft_record_id.name",
        "draft_record_id.is_group",
        "draft_record_id.given_name",
        "draft_record_id.family_name",
        "draft_record_id.phone",
        "draft_record_id.region",
    )
    def _compute_draft_fields(self):
        """Compute draft record fields for display with optimized dependencies."""
        for record in self:
            if record.draft_record_id:
                draft = record.draft_record_id
                record.draft_name = draft.name
                record.draft_is_group = draft.is_group
                record.draft_given_name = draft.given_name
                record.draft_family_name = draft.family_name
                record.draft_phone = draft.phone
                record.draft_region = draft.region
            else:
                record.draft_name = ""
                record.draft_is_group = False
                record.draft_given_name = ""
                record.draft_family_name = ""
                record.draft_phone = ""
                record.draft_region = ""

    @api.depends(
        "registrant_id",
        "registrant_id.given_name",
        "registrant_id.family_name",
        "registrant_id.phone",
        "registrant_id.region",
    )
    def _compute_registrant_fields(self):
        """Compute registrant fields for display with optimized dependencies."""
        for record in self:
            if record.registrant_id:
                registrant = record.registrant_id
                record.registrant_given_name = getattr(registrant, "given_name", "")
                record.registrant_family_name = getattr(registrant, "family_name", "")
                record.registrant_phone = registrant.phone if hasattr(registrant, "phone") else ""
                record.registrant_region = getattr(registrant, "region", "")
            else:
                record.registrant_given_name = ""
                record.registrant_family_name = ""
                record.registrant_phone = ""
                record.registrant_region = ""

    @api.constrains("type", "registrant_id")
    def _check_registrant_required_for_modify_delete(self):
        """Ensure registrant_id is set for modify and delete requests."""
        for record in self:
            if record.type in ["modify", "delete"] and not record.registrant_id:
                raise ValidationError(
                    _("Registrant must be specified for " "modify and delete change requests.")
                )

    @api.onchange("registrant_id")
    def _onchange_registrant_id(self):
        """Update is_group field when registrant is selected for modify requests."""
        if self.registrant_id and self.type == "modify":
            self.is_group = self.registrant_id.is_group

    @api.onchange("is_group")
    def _onchange_is_group(self):
        """Auto-select group_kind if only one exists when is_group is True."""
        if self.is_group and self.type == "create":
            group_kinds = self.env["g2p.group.kind"].search([])
            if len(group_kinds) == 1:
                self.group_kind_id = group_kinds.id

    @api.constrains("type", "is_group", "group_kind_id")
    def _check_group_kind_required_for_groups(self):
        """Ensure group_kind_id is set for group create requests."""
        for record in self:
            if record.type == "create" and record.is_group and not record.group_kind_id:
                raise ValidationError(_("Group Kind is required when creating a group change request."))

    @api.constrains("state", "draft_record_id")
    def _check_draft_record_consistency(self):
        """Ensure draft record exists when required based on state and type."""
        for record in self:
            if record.state in ["submitted", "approved"] and record.type in ["create", "modify"]:
                if not record.draft_record_id:
                    raise ValidationError(
                        _("Draft record is required for %(type)s requests in %(state)s state.")
                        % {
                            "type": record.type,
                            "state": record.state,
                        }
                    )

    @api.constrains("registrant_id", "type", "state")
    def _check_registrant_consistency(self):
        """Ensure registrant consistency based on change request type."""
        for record in self:
            # Only apply registrant_id validation during draft and submitted states
            # During approved state, registrant_id may be set by the approval process
            if record.state in ["draft", "submitted"]:
                if record.type == "create" and record.registrant_id:
                    raise ValidationError(
                        _(
                            "Registrant should not be specified for create requests. "
                            "A new registrant will be created upon approval."
                        )
                    )
                elif record.type in ["modify", "delete"] and not record.registrant_id:
                    raise ValidationError(_("Registrant must be specified for %s requests.") % record.type)

    @api.constrains("state")
    def _check_state_transitions(self):
        """Validate state transitions based on business rules."""
        for record in self:
            if record.state == "approved" and not record.approver_id:
                raise ValidationError(_("Approver must be set when state is approved."))
            elif record.state == "rejected" and not record.approver_id:
                raise ValidationError(_("Approver must be set when state is rejected."))

    @api.depends("type", "is_group", "group_kind_id")
    def _compute_validation_summary(self):
        """Compute validation summary for the change request."""
        for record in self:
            validation_errors = []

            # Check required fields based on type
            if record.type == "create":
                if record.is_group and not record.group_kind_id:
                    validation_errors.append("Group Kind is required for group creation")

            elif record.type in ["modify", "delete"]:
                if not record.registrant_id:
                    validation_errors.append("Registrant must be specified")

            # Check state consistency
            if record.state in ["submitted", "approved"] and record.type in ["create", "modify"]:
                if not record.draft_record_id:
                    validation_errors.append("Draft record is required")

            record.validation_summary = "; ".join(validation_errors) if validation_errors else "Valid"
            record.has_validation_errors = bool(validation_errors)

    @api.depends("state", "has_validation_errors", "draft_record_id", "type")
    def _compute_can_submit(self):
        """Compute whether the change request can be submitted."""
        for record in self:
            record.can_submit = (
                record.state == "draft"
                and not record.has_validation_errors
                and record.type in ["create", "modify"]
                and record.draft_record_id is not None
            )

    @api.depends("state", "requester_id")
    def _compute_can_approve(self):
        """Compute whether the change request can be approved."""
        for record in self:
            user = self.env.user
            record.can_approve = record.state == "submitted" and user.has_group(
                "g2p_change_management.group_change_management_approver"
            )

    @api.depends("state", "requester_id")
    def _compute_can_reject(self):
        """Compute whether the change request can be rejected."""
        for record in self:
            user = self.env.user
            record.can_reject = record.state == "submitted" and user.has_group(
                "g2p_change_management.group_change_management_approver"
            )

    @api.constrains("name")
    def _check_name_unique(self):
        """Ensure change request names are unique."""
        for record in self:
            if record.name and record.name != "New":
                existing = self.search([("name", "=", record.name), ("id", "!=", record.id)])
                if existing:
                    raise ValidationError(
                        _("Change request name '%s' already exists. Please use a unique name." % record.name)
                    )

    @api.constrains("registrant_id", "type", "state")
    def _check_duplicate_active_requests(self):
        """Prevent duplicate active change requests for the same registrant."""
        for record in self:
            if record.registrant_id and record.type in ["modify", "delete"]:
                active_requests = self.search(
                    [
                        ("registrant_id", "=", record.registrant_id.id),
                        ("type", "in", ["modify", "delete"]),
                        ("state", "in", ["draft", "submitted"]),
                        ("id", "!=", record.id),
                    ]
                )
                if active_requests:
                    msg = (
                        "There is already an active change request for registrant '%s'. "
                        "Please complete or cancel the existing request first."
                    )
                    raise ValidationError(msg % record.registrant_id.name)

    def _validate_before_submit(self):
        """Comprehensive validation before submitting a change request."""
        self.ensure_one()
        errors = []

        if self.type == "create":
            if self.is_group and not self.group_kind_id:
                errors.append("Group Kind is required for group creation requests")

        elif self.type in ["modify", "delete"]:
            if not self.registrant_id:
                errors.append("Registrant must be specified for modify/delete requests")
            else:
                # Check if registrant is active
                if not self.registrant_id.active:
                    errors.append("Cannot create change request for inactive registrant")

        # Draft record validation
        if self.type in ["create", "modify"] and not self.draft_record_id:
            errors.append("Draft record must be created before submitting")

        # State validation
        if self.state != "draft":
            errors.append("Only draft change requests can be submitted")

        if errors:
            raise ValidationError(
                _("Validation errors found:\n") + "\n".join("- " + error for error in errors)
            )

        return True

    def _update_group_member_statuses(self, new_state):
        self.ensure_one()

        if not self.draft_record_id or not self.draft_record_id.is_group:
            return 0

        member_ids = set()
        if self.draft_record_id.draft_member_ids:
            member_ids |= set(self.draft_record_id.draft_member_ids.ids)

        # Pass context to prevent recursive group processing
        ctx = dict(
            self.env.context,
            group_member_confirmed=True,
            group_cascade_processing=True,
            group_member_approval=True,
        )

        if new_state == "submitted":
            return self._cascade_group_submit(member_ids, ctx)
        elif new_state == "rejected":
            return self._cascade_group_reject(member_ids, ctx)
        elif new_state == "approved":
            return self.with_context(**ctx)._cascade_group_approve(member_ids, ctx)
        return 0

    def _cascade_group_submit(self, member_ids, ctx):
        updated = 0
        for draft_id in sorted(member_ids):
            member_cr = self._get_member_change_request(draft_id)
            if member_cr and member_cr.state == "draft":
                member_cr.sudo().write({"state": "submitted"})
                updated += 1
        return updated

    def _cascade_group_reject(self, member_ids, ctx):
        updated = 0
        for draft_id in sorted(member_ids):
            member_cr = self._get_member_change_request(draft_id)
            if member_cr and member_cr.state in ("draft", "submitted"):
                member_cr.sudo().write({"state": "rejected"})
                updated += 1
        return updated

    def _cascade_group_approve(self, member_ids, ctx):
        updated = 0
        failed = 0

        for draft_id in sorted(member_ids):
            member_cr = self._get_member_change_request(draft_id)

            if not member_cr:
                _logger.warning("No change request found for draft_id %s", draft_id)
                failed += 1
                continue

            if member_cr.state not in ("draft", "submitted"):
                _logger.info("Skipping member CR %s - already in state %s", member_cr.name, member_cr.state)
                continue

            try:
                # Check if this is a recursive call (member of a group)
                # If so, just implement changes without cascading
                if self.env.context.get("group_member_approval"):
                    # Update state and implement changes directly
                    member_cr.sudo().write(
                        {
                            "state": "approved",
                            "approver_id": self.env.user.id,
                        }
                    )

                    # Log the approval
                    member_cr.message_post(
                        body=_("Change request approved by %(user)s (via group approval).")
                        % {"user": self.env.user.name},
                        subject=_("Change Request Approved: %(name)s") % {"name": member_cr.name},
                    )

                    # Implement changes (publish individual registrant)
                    member_cr._implement_changes()

                    # Send notification
                    member_cr._send_approval_result_notification("approved")

                    # Close activities
                    member_cr._close_related_activities()

                    updated += 1
                    _logger.info("Successfully approved member CR %s (via group)", member_cr.name)
                else:
                    # Normal approval workflow
                    member_cr.sudo().action_approve()
                    updated += 1
                    _logger.info("Successfully approved member CR %s", member_cr.name)

            except Exception as e:
                _logger.error("Failed to approve member CR %s: %s", member_cr.name, str(e))
                failed += 1

        # Log summary
        if updated > 0 or failed > 0:
            _logger.info("Group member approval cascade: %s approved, %s failed", updated, failed)

        return updated

    def _get_member_change_request(self, draft_id):
        ChangeRequest = self.env["g2p.change.request"]
        return ChangeRequest.search([("draft_record_id", "=", draft_id)], order="create_date desc", limit=1)

    def _get_group_member_info(self):
        """Get information about draft members in the group."""
        self.ensure_one()

        if not self.draft_record_id or not self.draft_record_id.is_group:
            return {"count": 0, "names": ""}

        draft_record = self.draft_record_id
        if not draft_record.group_member_ids_json:
            return {"count": 0, "names": ""}

        try:
            raw = draft_record.group_member_ids_json
            data = json.loads(raw) if isinstance(raw, str) else raw
            draft_members = []

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("draft_id"):
                        draft_individual = self.env["g2p.draft.record"].browse(item["draft_id"])
                    elif isinstance(item, int):
                        draft_individual = self.env["g2p.draft.record"].browse(item)
                    else:
                        continue
                    if draft_individual.exists():
                        draft_members.append(draft_individual.name)

            return {
                "count": len(draft_members),
                "names": "\n".join(draft_members) if draft_members else "No draft members found",
            }

        except Exception:
            return {"count": 0, "names": _("Error reading member data")}

    def action_submit(self):
        """Submit the change request for approval."""
        self.ensure_one()

        # Comprehensive validation before submission
        self._validate_before_submit()

        # Validate approvers exist
        approvers = self.env["res.users"].search(
            [("groups_id", "in", self.env.ref("g2p_change_management.group_change_management_approver").id)]
        )
        if not approvers:
            raise UserError(_("No approvers found. Please contact your administrator."))

        # Update state
        self.write({"state": "submitted"})

        # Log the submission
        self.message_post(
            body=_("Change request submitted for approval by %s.") % self.env.user.name,
            subject=_("Change Request Submitted: %s") % self.name,
        )

        # Create activity for approvers
        self._create_approval_activity()

        # Update group member statuses if this is a group request
        if self.draft_record_id and self.draft_record_id.is_group:
            updated_count = self._update_group_member_statuses("submitted")
            if updated_count > 0:
                self.message_post(
                    body=_("Updated status of %s draft individual members to 'submitted'.") % updated_count,
                    subject=_("Group Member Status Updated"),
                )

        _logger.info("Change request %s submitted for approval by %s", self.name, self.env.user.name)
        return True

    def action_approve(self):
        """Approve the change request."""
        self.ensure_one()

        # Validate state
        if self.state != "submitted":
            raise UserError(_("Only submitted change requests can be approved."))

        # Validate permissions
        if not self.env.user.has_group("g2p_change_management.group_change_management_approver"):
            raise UserError(_("You don't have permission to approve change requests."))

        # Update state
        self.write(
            {
                "state": "approved",
                "approver_id": self.env.user.id,
            }
        )

        # Log the approval
        self.message_post(
            body=_("Change request approved by %(user)s.") % {"user": self.env.user.name},
            subject=_("Change Request Approved: %(name)s") % {"name": self.name},
        )

        # For groups, approve members FIRST before implementing group creation
        if self.is_group and self.draft_record_id and self.draft_record_id.is_group:
            updated_count = self._update_group_member_statuses("approved")
            if updated_count > 0:
                self.message_post(
                    body=_("Approved %s draft individual members.") % updated_count,
                    subject=_("Group Members Approved"),
                )
                _logger.info("Group CR %s: Approved %s member change requests", self.name, updated_count)

        # Now implement the changes (create group registrant and link members)
        try:
            self._implement_changes()
            _logger.info("Changes implemented successfully for change request %s", self.name)
        except Exception as err:
            _logger.error("Failed to implement changes for change request %s: %s", self.name, str(err))
            raise UserError(_("Failed to implement changes: %s") % str(err)) from err

        # Send notification to requester
        self._send_approval_result_notification("approved")

        # Close related activities
        self._close_related_activities()

        _logger.info("Change request %s approved by %s", self.name, self.env.user.name)
        return True

    def action_reject(self):
        """Reject the change request."""
        self.ensure_one()

        # Validate state
        if self.state != "submitted":
            raise UserError(_("Only submitted change requests can be rejected."))

        # Validate permissions
        if not self.env.user.has_group("g2p_change_management.group_change_management_approver"):
            raise UserError(_("You don't have permission to reject change requests."))

        # Open rejection wizard to capture reason
        action = self.env.ref("g2p_change_management.action_change_request_reject_wizard").read()[0]
        action["context"] = {
            **self.env.context,
            "default_change_request_id": self.id,
        }
        return action

    def _create_approval_activity(self):
        """Create approval activity for approvers."""
        approvers = self.env["res.users"].search(
            [("groups_id", "in", self.env.ref("g2p_change_management.group_change_management_approver").id)]
        )

        if not approvers:
            _logger.warning("No approvers found for change request %s", self.name)
            return

        # Calculate deadline (3 business days from now)
        deadline = fields.Date.today()
        for _ in range(3):  # noqa: F402
            deadline = deadline + timedelta(days=1)
            # Skip weekends (simple implementation)
            while deadline.weekday() >= 5:  # Saturday = 5, Sunday = 6
                deadline = deadline + timedelta(days=1)

        for approver in approvers:
            # Create activity
            activity = self.env["mail.activity"].create(
                {
                    "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                    "note": (
                        f"Change request '{self.name}' requires your approval.\n\n"
                        f"Type: {dict(self._fields['type'].selection).get(self.type, self.type)}\n"
                        f"Requester: {self.requester_id.name}\n"
                    ),
                    "res_id": self.id,
                    "res_model_id": self.env["ir.model"]._get("g2p.change.request").id,
                    "user_id": approver.id,
                    "date_deadline": deadline,
                }
            )

            # Send email notification
            self._send_approval_notification(approver, activity)

    def _send_approval_notification(self, approver, activity):
        """Send email notification to approver."""
        try:
            template = self.env.ref(
                "g2p_change_management.mail_template_change_request_approval", raise_if_not_found=False
            )
            if template:
                template.with_context(activity_id=activity.id).send_mail(self.id, force_send=True)
            else:
                # Fallback: send simple notification
                self.message_post(
                    body=_("Approval notification sent to %s") % approver.name,
                    registrant_ids=[approver.registrant_id.id] if approver.registrant_id else [],
                    subject=_("Change Request Approval Required: %s") % self.name,
                )
        except Exception as e:
            _logger.error("Failed to send approval notification to %s: %s", approver.name, str(e))

    def _send_approval_result_notification(self, result):
        """Send notification to requester about approval result."""
        try:
            if result == "approved":
                subject = _("Change Request Approved: %(name)s") % {"name": self.name}
                body = _("Your change request '%(name)s' has been approved by %(approver)s.") % {
                    "name": self.name,
                    "approver": self.approver_id.name,
                }
            else:  # rejected
                subject = _("Change Request Rejected: %(name)s") % {"name": self.name}
                body = _("Your change request '%(name)s' has been rejected by %(approver)s.") % {
                    "name": self.name,
                    "approver": self.approver_id.name,
                }

            self.message_post(
                body=body,
                subject=subject,
                registrant_ids=[self.requester_id.registrant_id.id]
                if self.requester_id.registrant_id
                else [],
            )
        except Exception as e:
            _logger.error("Failed to send approval result notification: %s", str(e))

    def _close_related_activities(self):
        """Close all activities related to this change request."""
        try:
            activities = self.env["mail.activity"].search(
                [
                    ("res_id", "=", self.id),
                    ("res_model", "=", "g2p.change.request"),
                    ("state", "=", "planned"),
                ]
            )
            activities.write({"state": "done"})
            _logger.info("Closed %s activities for change request %s", len(activities), self.name)
        except Exception as e:
            _logger.error("Failed to close activities for change request %s: %s", self.name, str(e))

    def _implement_changes(self):
        self.ensure_one()
        if self.type == "create":
            self._implement_create()
        elif self.type == "modify":
            self._implement_modify()
        elif self.type == "delete":
            self._implement_delete()

    def _implement_create(self):
        if not self.draft_record_id:
            return

        # Capture new values from draft record before publishing
        new_values = self._get_draft_record_values()

        # Publish the draft record to create a new registrant
        # Use force_write context to bypass write protection during publishing
        created_registrant = self.draft_record_id.with_context(force_write=True).action_publish()
        if created_registrant:
            # Link the created registrant to this change request
            self.write({"registrant_id": created_registrant.id})

            # For groups, link already-approved member registrants to the group
            if self.is_group:
                self._link_approved_members_to_group(created_registrant.id)

            # Create change log entry for creation
            self.env["g2p.change.log"].create_change_log(
                change_request=self,
                registrant=created_registrant,
                change_type="create",
                new_values=new_values,
            )

            # Update the change request name with the new registrant name and unique_id
            unique_id = getattr(created_registrant, "unique_id", "")
            if unique_id:
                self.name = f"{created_registrant.name} ({unique_id}) - CR #{self.id}"
            else:
                self.name = f"{created_registrant.name} - CR #{self.id}"
            self.message_post(
                body=_("New registrant '%s' has been created and published to the registry.")
                % created_registrant.name,
                subject=_("Registrant Created: %s") % created_registrant.name,
            )
            _logger.info(
                "Registrant created successfully: %s (ID: %s)", created_registrant.name, created_registrant.id
            )

    def _implement_modify(self):
        if not self.registrant_id or not self.draft_record_id:
            return
        # Capture old values from existing registrant before modification
        old_values = self._get_registrant_values(self.registrant_id)

        # Capture new values from draft record
        new_values = self._get_draft_record_values()

        # For modify requests, we need to update the existing registrant instead of creating a new one
        # Get the data from the draft record and update the existing registrant
        registrant_data = json.loads(self.draft_record_id.registrant_data)

        # Prepare update data
        update_data = {}
        if registrant_data.get("is_group"):
            group_name = (registrant_data.get("name") or "").strip().upper()
            update_data["name"] = group_name
            update_data["is_group"] = True
        else:
            given_name = (registrant_data.get("given_name") or "").strip()
            family_name = (registrant_data.get("family_name") or "").strip()
            addl_name = (registrant_data.get("addl_name") or "").strip()
            update_data["name"] = f"{given_name} {family_name} {addl_name}".strip().upper()
            update_data["is_group"] = False

        # Add other fields from registrant_data
        for field_name in [
            "given_name",
            "family_name",
            "addl_name",
            "phone",
            "email",
            "gender",
            "region",
        ]:
            if field_name in registrant_data and registrant_data[field_name]:
                update_data[field_name] = registrant_data[field_name]

        # Update the existing registrant with force_write context
        self.registrant_id.with_context(force_write=True).write(update_data)

        # Create change log entry for modification
        self.env["g2p.change.log"].create_change_log(
            change_request=self,
            registrant=self.registrant_id,
            change_type="modify",
            old_values=old_values,
            new_values=new_values,
        )

        # Update the change request name with the updated registrant name and unique_id
        unique_id = getattr(self.registrant_id, "unique_id", "")
        if unique_id:
            self.name = f"{self.registrant_id.name} ({unique_id}) - CR #{self.id}"
        else:
            self.name = f"{self.registrant_id.name} - CR #{self.id}"
        self.message_post(
            body=_("Registrant '%s' has " "been updated in the registry.") % self.registrant_id.name,
            subject=_("Registrant Updated: %s") % self.registrant_id.name,
        )
        _logger.info(
            "Registrant updated successfully: %s (ID: %s)", self.registrant_id.name, self.registrant_id.id
        )

    def _implement_delete(self):
        if not self.registrant_id:
            return
        # Capture old values from registrant before deletion
        old_values = self._get_registrant_values(self.registrant_id)

        # Use force_write context to bypass write protection during deletion
        self.registrant_id.with_context(force_write=True).write({"active": False})

        # Create change log entry for deletion
        self.env["g2p.change.log"].create_change_log(
            change_request=self, registrant=self.registrant_id, change_type="delete", old_values=old_values
        )

        self.message_post(body=_("Registrant '%s' has been deactivated.") % self.registrant_id.name)

    def _link_approved_members_to_group(self, group_registrant_id):
        self.ensure_one()

        if not self.draft_record_id or not self.draft_record_id.draft_member_ids:
            return

        membership_model = self.env["g2p.group.membership"].sudo()
        linked_count = 0
        skipped_count = 0

        for draft_member in self.draft_record_id.draft_member_ids:
            member_cr = self._get_member_change_request(draft_member.id)

            if not member_cr:
                skipped_count += 1
                continue

            if member_cr.state == "approved" and member_cr.registrant_id:
                existing_membership = membership_model.search(
                    [("group", "=", group_registrant_id), ("individual", "=", member_cr.registrant_id.id)],
                    limit=1,
                )

                if not existing_membership:
                    membership_model.create(
                        {
                            "group": group_registrant_id,
                            "individual": member_cr.registrant_id.id,
                        }
                    )
                    linked_count += 1
                else:
                    linked_count += 1
            else:
                skipped_count += 1

        if linked_count > 0 or skipped_count > 0:
            self.message_post(
                body=_(
                    "Group membership linking completed:\n"
                    "- Successfully linked: %(linked_count)s members\n- Skipped: %(skipped_count)s members"
                )
                % {"linked_count": linked_count, "skipped_count": skipped_count},
                subject=_("Group Members Linked"),
            )

    def _get_registrant_values(self, registrant):
        """Get current values from a registrant record for change logging."""
        try:
            # Get the most relevant fields for change tracking
            registrant_values = {
                "name": registrant.name,
                "is_group": getattr(registrant, "is_group", False),
                "given_name": getattr(registrant, "given_name", ""),
                "family_name": getattr(registrant, "family_name", ""),
                "addl_name": getattr(registrant, "addl_name", ""),
                "phone": registrant.phone or "",
                "email": registrant.email or "",
                "gender": getattr(registrant, "gender", ""),
                "active": registrant.active,
            }

            # Add region if it exists
            if hasattr(registrant, "region") and registrant.region:
                if hasattr(registrant.region, "id"):
                    registrant_values["region"] = registrant.region.id
                else:
                    registrant_values["region"] = registrant.region

            # Add group kind if it's a group
            if getattr(registrant, "is_group", False) and hasattr(registrant, "kind") and registrant.kind:
                if hasattr(registrant.kind, "id"):
                    registrant_values["kind"] = registrant.kind.id
                else:
                    registrant_values["kind"] = registrant.kind

            return registrant_values

        except Exception as err:
            _logger.error("Error getting registrant values for %s: %s", registrant.name, str(err))
            return {"name": registrant.name, "error": "Failed to capture values"}

    def _get_draft_record_values(self):
        """Get values from draft record for change logging."""
        try:
            if not self.draft_record_id:
                return {}

            draft_record = self.draft_record_id
            draft_values = {
                "name": draft_record.name,
                "is_group": draft_record.is_group,
                "given_name": getattr(draft_record, "given_name", ""),
                "family_name": getattr(draft_record, "family_name", ""),
                "addl_name": getattr(draft_record, "addl_name", ""),
                "phone": getattr(draft_record, "phone", ""),
                "email": getattr(draft_record, "email", ""),
                "gender": getattr(draft_record, "gender", ""),
            }

            # Add region if it exists
            if hasattr(draft_record, "region") and draft_record.region:
                if hasattr(draft_record.region, "id"):
                    draft_values["region"] = draft_record.region.id
                else:
                    draft_values["region"] = draft_record.region

            # Add group kind if it's a group
            if draft_record.is_group and hasattr(draft_record, "kind") and draft_record.kind:
                if hasattr(draft_record.kind, "id"):
                    draft_values["kind"] = draft_record.kind.id
                else:
                    draft_values["kind"] = draft_record.kind

            # Also try to get data from registrant_data JSON if available
            if hasattr(draft_record, "registrant_data") and draft_record.registrant_data:
                try:
                    json_data = json.loads(draft_record.registrant_data)
                    # Merge JSON data, giving priority to direct field values
                    for key, value in json_data.items():
                        if key not in draft_values or not draft_values[key]:
                            draft_values[key] = value
                except (json.JSONDecodeError, TypeError) as err:
                    _logger.warning(
                        "Failed to parse registrant_data JSON for draft record %s: %s",
                        draft_record.id,
                        err,
                    )

            return draft_values

        except Exception as err:
            _logger.error("Error getting draft record values for %s: %s", self.name, str(err))
            return {
                "name": getattr(self.draft_record_id, "name", "Unknown"),
                "error": "Failed to capture values",
            }

    def _create_draft_record_for_different_type_cr(self):
        """Create a draft record based on the change request type."""
        self.ensure_one()

        _logger.info("Creating draft record for type: %s", self.type)

        if self.type == "create":
            # For create requests, use the is_group field from change request
            draft_data = {
                "name": f"New {'Group' if self.is_group else 'Individual'} - {self.id}",
                "is_group": self.is_group,
            }

            if self.is_group:
                # Create the draft record first, then update its JSON data
                draft_record = self.env["g2p.draft.record"].create(draft_data)

                # Update the JSON data to include group_kind_id if set
                registrant_data = json.loads(draft_record.registrant_data or "{}")
                if self.group_kind_id:
                    registrant_data["kind"] = self.group_kind_id.id
                draft_record.write({"registrant_data": json.dumps(registrant_data)})

                return draft_record

            # For individuals, create draft record
            _logger.info("Create request draft data: %s", draft_data)
            draft_record = self.env["g2p.draft.record"].create(draft_data)
            _logger.info("Draft record created successfully: %s", draft_record.name)
            return draft_record

        elif self.type == "modify":
            # For modify requests, copy registrant data to draft
            if not self.registrant_id:
                raise UserError(_("Registrant must be specified for modify requests."))

            # Get region value safely - convert Many2one to ID if it exists
            region_value = getattr(self.registrant_id, "region", "")
            if hasattr(region_value, "id"):
                region_value = region_value.id
            elif not region_value:
                region_value = ""

            draft_data = {
                "name": self.registrant_id.name,
                "is_group": self.registrant_id.is_group,
                "given_name": getattr(self.registrant_id, "given_name", ""),
                "family_name": getattr(self.registrant_id, "family_name", ""),
                "addl_name": getattr(self.registrant_id, "addl_name", ""),
                "phone": self.registrant_id.phone if hasattr(self.registrant_id, "phone") else "",
                "gender": getattr(self.registrant_id, "gender", ""),
                "region": region_value,
            }
            _logger.info("Modify request draft data: %s", draft_data)

            # Create the draft record for modify
            _logger.info("Attempting to create draft record with data: %s", draft_data)
            draft_record = self.env["g2p.draft.record"].create(draft_data)
            _logger.info("Draft record created successfully: %s", draft_record.name)
            return draft_record

        elif self.type == "delete":
            # For delete requests, no draft record needed
            _logger.info("Delete request - no draft record created")
            return None

        else:
            raise UserError(_("Invalid change request type."))

    def action_edit_draft_record(self):
        """Open the draft record in edit mode using existing draft record methods."""
        self.ensure_one()

        if not self.draft_record_id:
            raise UserError(_("No draft record to edit."))

        # Use the draft record's existing action methods with proper context
        if self.draft_record_id.is_group:
            action = self.draft_record_id.action_open_group_wizard()
        else:
            action = self.draft_record_id.action_open_individual_wizard()

        # Update the context to point to the draft record instead of change request
        if action and "context" in action:
            action["context"].update(
                {
                    "active_model": "g2p.draft.record",
                    "active_id": self.draft_record_id.id,
                    "change_request_context": True,  # Add change request context for filtering
                }
            )

        return action

    def _return_wizard_with_context(self, view_id):
        """Return wizard action with proper context for registrant form."""
        self.ensure_one()
        active_id = self.id

        if not self.registrant_data:
            raise UserError(_("No registrant data available."))

        try:
            json_data = json.loads(self.registrant_data)
        except json.JSONDecodeError as err:
            raise UserError(_("Invalid JSON data in registrant_data.")) from err

        context_data, additional_g2p_info = self._process_json_data(json_data)

        context_data["active_id"] = active_id

        _logger.info("Additional info")
        _logger.info(additional_g2p_info)
        return {
            "type": "ir.actions.act_window",
            "name": "Registrant Data",
            "view_mode": "form",
            "res_model": "res.partner",
            "view_id": view_id,
            "target": "new",
            "context": {
                **context_data,
                "default_additional_g2p_info": json.dumps(additional_g2p_info),
                "draft": "yes",
                "default_phone_number_ids": json_data.get("phone_number_ids", []),
                "default_individual_membership_ids": json_data.get("individual_membership_ids", []),
                "default_reg_ids": json_data.get("reg_ids", []),
                "default_is_group": json_data.get("is_group", False),
            },
        }

    def _process_json_data(self, json_data):
        """Process JSON data for registrant form context."""
        partner_model_fields = self.env["res.partner"]._fields
        additional_g2p_info = {}
        context_data = {}

        for field_name, field_value in json_data.items():
            if field_name not in partner_model_fields:
                continue
            field = partner_model_fields[field_name]
            self._process_field(field_name, field, field_value, context_data, additional_g2p_info)

        return context_data, additional_g2p_info

    def _process_field(self, field_name, field, field_value, context_data, additional_g2p_info):
        """Handle individual field based on type."""
        if field.type == "datetime" and isinstance(field_value, str):
            context_data[f"default_{field_name}"] = datetime.fromisoformat(field_value)

        elif field.type == "date" and isinstance(field_value, str):
            context_data[f"default_{field_name}"] = date.fromisoformat(field_value)

        elif field.type in ("char", "text") and isinstance(field_value, str):
            context_data[f"default_{field_name}"] = field_value

        elif field.type == "many2one":
            if isinstance(field_value, int):
                context_data[f"default_{field_name}"] = field_value
            elif field_name in self._fields and field_value is not None:
                additional_g2p_info[field_name] = field_value

        elif field.type == "many2many" and isinstance(field_value, list):
            if all(isinstance(val, list) for val in field_value):
                items = [item[1] for item in field_value]
                context_data[f"default_{field_name}"] = [(6, 0, items)]

        elif field.type == "selection":
            selection_values = field.get_values(env=self.env)
            if field_value in selection_values:
                context_data[f"default_{field_name}"] = field_value
            elif field_name in self._fields and field_value is not None:
                additional_g2p_info[field_name] = field_value

        else:
            context_data[f"default_{field_name}"] = field_value

    # ==================== BULK OPERATIONS ====================

    def action_bulk_approve(self):
        """Open bulk approval wizard"""
        return self._open_bulk_wizard("approve")

    def action_bulk_reject(self):
        """Open bulk rejection wizard"""
        return self._open_bulk_wizard("reject")

    def action_bulk_submit(self):
        """Open bulk submission wizard"""
        return self._open_bulk_wizard("submit")

    def action_bulk_cancel(self):
        """Open bulk cancellation wizard"""
        return self._open_bulk_wizard("cancel")

    def action_bulk_assign(self):
        """Open bulk assignment wizard"""
        return self._open_bulk_wizard("assign")

    def _open_bulk_wizard(self, operation_type):
        """Open the bulk operations wizard"""
        if not self:
            raise UserError(_("No change requests selected for bulk operation."))

        # Validate that all selected records are change requests
        if not all(record._name == "g2p.change.request" for record in self):
            raise UserError(_("All selected records must be change requests."))

        return {
            "type": "ir.actions.act_window",
            "name": f"Bulk {operation_type.title()}",
            "res_model": "g2p.change.request.bulk.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_ids": self.ids,
                "operation_type": operation_type,
            },
        }
