import json
import logging
from datetime import date, datetime

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BaseInherit(models.AbstractModel):
    _inherit = "base"

    def web_save(self, vals, specification: dict[str, dict], next_id=None) -> list[dict]:
        if (
            self._name == "res.partner"
            and self.env.context.get("draft")
            and hasattr(self, "action_save_to_draft")
        ):
            self.action_save_to_draft(vals)
            return self

        if self:
            self.write(vals)
        else:
            self = self.create(vals)
        if next_id:
            self = self.browse(next_id)
        return self.with_context(bin_size=True).web_read(specification)


class G2PDraftRecord(models.Model):
    _name = "g2p.draft.record"
    _description = "Draft Records"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char()
    given_name = fields.Char()
    family_name = fields.Char()
    addl_name = fields.Char()
    phone = fields.Char()
    gender = fields.Char()
    region = fields.Char()
    is_group = fields.Boolean(default=False)
    registrant_data = fields.Json(string="Registrant Data (JSON)")
    group_member_ids_json = fields.Json(string="Group Members (JSON)", default=list)

    # Add One2many to link all change requests using this draft record
    change_request_ids = fields.One2many(
        "g2p.change.request",
        "draft_record_id",
        string="Change Requests",
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
        store=True,
        help="State of the active change request for this draft record",
    )

    # Draft members field - Many2many relationship for draft individual members
    draft_member_ids = fields.Many2many(
        "g2p.draft.record",
        "draft_group_member_rel",
        "group_id",
        "member_id",
        string="Draft Members",
        help="Draft individual members of this group",
        domain="[('is_group', '=', False)]",
    )

    def _return_wizard_with_context(self, view_id):
        """Override to filter out draft_member_ids from registrant_data before processing."""
        # Get the registrant_data and filter out draft_member_ids
        if self.registrant_data:
            try:
                json_data = json.loads(self.registrant_data)
                # Remove draft_member_ids if it exists
                if "draft_member_ids" in json_data:
                    del json_data["draft_member_ids"]
                # Update the registrant_data with filtered data
                self.registrant_data = json.dumps(json_data)
            except (json.JSONDecodeError, KeyError) as err:
                _logger.warning(
                    "Failed to filter draft_member_ids from registrant_data JSON for draft record %s: %s",
                    self.id,
                    err,
                )
        return super()._return_wizard_with_context(view_id)

    @api.depends("change_request_ids.state")
    def _compute_active_change_request_state(self):
        """Compute the state of the active change request for this draft record."""
        for record in self:
            # Find the most recent change request for this draft record
            change_request = record.change_request_ids.sorted("create_date", reverse=True)[:1]
            if change_request:
                change_request = change_request[0]
                record.active_change_request_state = change_request.state
                _logger.info(
                    "Draft Record %s: active_change_request_state = %s",
                    record.id,
                    change_request.state,
                )
            else:
                record.active_change_request_state = False
                _logger.info(f"Draft Record {record.id}: No change request found, state = False")

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        """Override name search to filter by
        group type and Change Request states
        when in member selection context."""
        args = args or []

        # Check if we're in a member selection context (from change request or group wizard)
        if self.env.context.get("member_selection_context") or self.env.context.get("change_request_context"):
            args += [("is_group", "=", False)]

            # Get all individual draft records
            draft_records = self.env["g2p.draft.record"].search(args)

            # Filter based on Change Request states
            allowed_states = ["draft", "submitted"]
            filtered_records = self.env["g2p.draft.record"]

            for draft_record in draft_records:
                # Check if this draft record has any Change Requests in allowed states
                change_requests = self.env["g2p.change.request"].search(
                    [("draft_record_id", "=", draft_record.id), ("state", "in", allowed_states)]
                )

                # Only include if it has Change Requests in allowed states (draft or submitted)
                if change_requests.exists():
                    filtered_records |= draft_record

            # Apply name search on filtered records
            if name:
                filtered_records = filtered_records.filtered(lambda r: name.lower() in r.name.lower())

            return filtered_records.ids[:limit]

        return super()._name_search(name, args, operator, limit, name_get_uid)

    def name_get(self):
        """Override name_get to filter by group type
        and Change Request states when in member
        selection context."""
        if self.env.context.get("member_selection_context") or self.env.context.get("change_request_context"):
            # Filter records to only show individual records (not groups)
            filtered_records = self.filtered(lambda r: not r.is_group)

            # Further filter based on Change Request states
            allowed_states = ["draft", "submitted"]
            final_filtered_records = self.env["g2p.draft.record"]

            for draft_record in filtered_records:
                # Check if this draft record has any Change Requests in allowed states
                change_requests = self.env["g2p.change.request"].search(
                    [("draft_record_id", "=", draft_record.id), ("state", "in", allowed_states)]
                )

                # Only include if it has Change Requests in allowed states (draft or submitted)
                if change_requests.exists():
                    final_filtered_records |= draft_record

            # Add Change Request state information to the display name
            result = []
            for record in final_filtered_records:
                # Find the most recent Change Request for this draft record
                change_request = self.env["g2p.change.request"].search(
                    [("draft_record_id", "=", record.id), ("state", "in", allowed_states)],
                    order="create_date desc",
                    limit=1,
                )

                if change_request:
                    display_name = f"{record.name} (CR: {change_request.state})"
                else:
                    display_name = record.name

                result.append((record.id, display_name))

            return result

        return super().name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Override search to filter by Change Request states when in member selection context."""

        _logger.info(f"SEARCH CALLED - Context: {self.env.context}")

        # Only apply custom filtering in member selection context
        if self.env.context.get("member_selection_context"):
            _logger.info("MEMBER SELECTION CONTEXT DETECTED - Applying filtering")
            try:
                # Get all individual draft records first
                args = args or []
                args += [("is_group", "=", False)]

                # Use super().search to avoid recursion
                draft_records = super().search(args)

                # Filter based on Change Request states
                allowed_states = ["draft", "submitted"]
                filtered_records = self.env["g2p.draft.record"]

                for draft_record in draft_records:
                    # Check if this draft record has any Change Requests in allowed states
                    change_requests = self.env["g2p.change.request"].search(
                        [("draft_record_id", "=", draft_record.id), ("state", "in", allowed_states)]
                    )

                    # Only include if it has Change Requests in allowed states
                    if change_requests.exists():
                        filtered_records |= draft_record

                if count:
                    return len(filtered_records)

                # Apply offset and limit
                if offset:
                    filtered_records = filtered_records[offset:]
                if limit:
                    filtered_records = filtered_records[:limit]

                return filtered_records.ids
            except Exception as e:
                # If there's any error, fall back to normal search
                _logger.warning(f"Error in member selection search: {e}")
                pass

        return super().search(args, offset, limit, order)

    @api.model
    def create(self, vals):
        partner_data = {}
        is_group = vals.get("is_group", False)
        vals["is_group"] = is_group

        if vals.get("is_group"):
            partner_data["name"] = vals.get("name", "")
            partner_data["is_group"] = True
        else:
            given_name = vals.get("given_name", "")
            family_name = vals.get("family_name", "")
            addl_name = vals.get("addl_name", "")
            partner_data = {
                "given_name": given_name,
                "family_name": family_name,
                "addl_name": addl_name,
                "gender": vals.get("gender", ""),
                "region": vals.get("region", ""),
                "is_group": False,
            }
            vals["name"] = f"{given_name} {family_name} {addl_name}".strip().upper()

        if vals.get("phone"):
            partner_data["phone_number_ids"] = [(0, 0, {"phone_no": vals["phone"]})]

        partner_data["imported_record_state"] = "draft"
        vals["registrant_data"] = json.dumps(partner_data)

        return super().create(vals)

    def action_change_state(self):
        return {
            "name": "Confirm Rejection",
            "type": "ir.actions.act_window",
            "res_model": "change.state.wizard",
            "view_mode": "form",
            "view_id": self.env.ref("g2p_change_management.change_state_wizard_view").id,
            "target": "new",
        }

    def action_publish(self):
        self.ensure_one()
        registrant_data = json.loads(self.registrant_data)
        res_partner_model = self.env["res.partner"]
        fields_metadata = res_partner_model.fields_get()
        valid_data = {}
        created_partner = None

        self._prepare_valid_data(valid_data, fields_metadata, registrant_data)

        if valid_data:
            valid_data["db_import"] = "yes"
            valid_data["is_registrant"] = True
        else:
            raise ValueError("No valid data found to create a partner record.")

        if registrant_data.get("is_group"):
            group_name = (registrant_data.get("name") or "").strip().upper()
            valid_data["name"] = group_name
            valid_data["is_group"] = True
        else:
            given_name = (registrant_data.get("given_name") or "").strip()
            family_name = (registrant_data.get("family_name") or "").strip()
            addl_name = (registrant_data.get("addl_name") or "").strip()
            valid_data["name"] = f"{given_name} {family_name} {addl_name}".strip().upper()
            valid_data["is_group"] = False

        created_partner = res_partner_model.sudo().create(valid_data)
        if registrant_data.get("is_group"):
            _logger.info(
                "Group partner %s created. Members will be linked after their approval.", created_partner.name
            )

        self._notify_validators()
        return created_partner

    def _prepare_valid_data(self, valid_data, fields_metadata, registrant_data):
        """Prepare valid data for partner creation based on field types."""
        validators = {
            "char": lambda v, f: isinstance(v, str),
            "text": lambda v, f: isinstance(v, str),
            "integer": lambda v, f: isinstance(v, int),
            "float": lambda v, f: isinstance(v, int | float),
            "boolean": lambda v, f: isinstance(v, bool),
            "many2one": lambda v, f: isinstance(v, int) and self.env[f["relation"]].browse(v).exists(),
            "many2many": lambda v, f: isinstance(v, list)
            and all(self.env[f["relation"]].browse(x[1]).exists() for x in v),
            "one2many": lambda v, f: isinstance(v, list),
            "datetime": lambda v, f: True,
            "date": lambda v, f: True,
            "selection": lambda v, f: v in [option[0] for option in f.get("selection", [])],
        }

        for field_name, value in registrant_data.items():
            if field_name not in fields_metadata:
                continue

            field_info = fields_metadata[field_name]
            field_type = field_info.get("type")

            if validators.get(field_type, lambda v, f: False)(value, field_info):
                valid_data[field_name] = value

        # return valid_data

    def _prepare_field_value(self, field_type, value, field_info):
        """Prepare field value for storage."""
        preparers = {
            "float": lambda v: float(v),
            "many2many": lambda v: v,
            "one2many": lambda v: [(0, 0, x[2]) for x in v],
            "datetime": lambda v: v,
            "date": lambda v: v,
            "selection": lambda v: v,
            "many2one": lambda v: v,
            "boolean": lambda v: v,
            "char": lambda v: v,
            "text": lambda v: v,
        }

        return preparers.get(field_type, lambda v: v)(value)

    def _notify_validators(self):
        """Notify appropriate validator users about the published record."""
        validator_group = self.env.ref("g2p_change_management.group_change_management_user")
        admin_group = self.env.ref("g2p_change_management.group_change_management_admin")
        approver_group = self.env.ref("g2p_change_management.group_change_management_approver")

        validator_users = validator_group.users
        exclusive_validator_users = validator_users.filtered(
            lambda user: user not in admin_group.users and user not in approver_group.users
        )

        matching_users = exclusive_validator_users.filtered(
            lambda user: user.partner_id.id in self.message_partner_ids.ids
        )

        if matching_users:
            for user in matching_users:
                self.sudo().message_post(
                    body=_("Record has been published"),
                    subject=_("Record Published"),
                    message_type="notification",
                    partner_ids=[user.partner_id.id],
                )
        self.message_partner_ids = [(4, self.env.user.partner_id.id)]

    def action_submit(self):
        for record in self:
            registrant_data = json.loads(record.registrant_data)
            registrant_data["imported_record_state"] = "submitted"

            if registrant_data.get("is_group"):
                individual_draft_ids = record.group_member_ids_json or []
                for draft_id in individual_draft_ids:
                    draft_individual = self.env["g2p.draft.record"].browse(draft_id)
                    if draft_individual.exists():
                        draft_individual.action_submit()

            self.write({"state": "submitted", "registrant_data": json.dumps(registrant_data)})
            activities = self.env["mail.activity"].search(
                [("res_model", "=", self._name), ("res_id", "in", self.ids)]
            )
            if activities:
                activities.action_done()

            approver_group = self.env.ref("g2p_change_management.group_int_approver")
            approver_users = approver_group.users
            if approver_users:
                for user in approver_users:
                    self.sudo().env["mail.activity"].create(
                        {
                            "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                            "res_model_id": self.sudo()
                            .env["ir.model"]
                            .search([("model", "=", "g2p.draft.record")])
                            .id,
                            "res_id": record.id,
                            "user_id": user.id,
                            "summary": "Record Submitted For Approval",
                            "note": "Record have been Submitted For Approval!",
                        }
                    )

    def _return_wizard_with_context(self, view_id):
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

        _logger.info("The Additionla info")
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
                "change_request_state": self.active_change_request_state,
                "default_phone_number_ids": json_data.get("phone_number_ids", []),
                "default_individual_membership_ids": json_data.get("individual_membership_ids", []),
                "default_reg_ids": json_data.get("reg_ids", []),
                "default_is_group": json_data.get("is_group", False),
            },
        }

    def action_open_individual_wizard(self):
        return self._return_wizard_with_context(
            self.env.ref("g2p_change_management.g2p_validation_individual_form_view").id
        )

    def action_open_individual_wizard_view_only(self):
        return self._return_wizard_with_context(
            self.env.ref("g2p_change_management.g2p_validation_individual_form_view_only").id
        )

    def action_open_group_wizard(self):
        return self._return_wizard_with_context(
            self.env.ref("g2p_change_management.g2p_validation_group_form_view").id
        )

    def action_open_group_wizard_view_only(self):
        return self._return_wizard_with_context(
            self.env.ref("g2p_change_management.g2p_validation_group_form_view_only").id
        )

    def _process_json_data(self, json_data):
        partner_model_fields = self.env["res.partner"]._fields
        additional_g2p_info = {}
        context_data = {}

        for field_name, field_value in json_data.items():
            field = partner_model_fields[field_name]

            if field.type == "datetime" and isinstance(field_value, str):
                field_value = datetime.fromisoformat(field_value)
                context_data[f"default_{field_name}"] = field_value

            elif field.type == "date" and isinstance(field_value, str):
                field_value = date.fromisoformat(field_value)
                context_data[f"default_{field_name}"] = field_value

            elif (field.type == "char" or field.type == "text") and isinstance(field_value, str):
                context_data[f"default_{field_name}"] = field_value

            elif field.type == "many2one":
                if isinstance(field_value, int):
                    field_value = int(field_value)
                    context_data[f"default_{field_name}"] = json_data[field_name]
                else:
                    if field_name in self._fields and field_value is not None:
                        additional_g2p_info[field_name] = field_value

            elif field.type == "many2many":
                _logger.info(field_value)
                if isinstance(field_value, list):
                    if all(isinstance(val, list) for val in field_value):
                        items = []
                        for item in field_value:
                            items.append(item[1])

                        context_data[f"default_{field_name}"] = [(6, 0, items)]

            elif field.type == "selection":
                selection_values = field.get_values(env=self.env)

                if field_value in selection_values:
                    context_data[f"default_{field_name}"] = field_value

                if field_value not in selection_values:
                    if field_name in self._fields and field_value is not None:
                        additional_g2p_info[field_name] = field_value

            else:
                context_data[f"default_{field_name}"] = field_value

        return context_data, additional_g2p_info

    def action_reject(self):
        return {
            "name": "Confirm Rejection",
            "type": "ir.actions.act_window",
            "res_model": "g2p.reject.wizard",
            "view_mode": "form",
            "target": "new",
        }


class G2PRespartnerIntegration(models.Model):
    _inherit = "res.partner"

    db_import = fields.Selection(
        string="Imported", index=True, selection=[("yes", "Yes"), ("no", "No")], default="no"
    )

    imported_record_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("published", "Published"),
            ("rejected", "Rejected"),
        ],
        default="draft",
    )

    def action_update(self):
        return

    def action_save_to_draft(self, vals):
        context = self.env.context
        model_name = context.get("active_model")
        record_id = context.get("active_id")
        active_record = self.env[model_name].browse(record_id)
        registrant_data = json.loads(active_record.registrant_data or "{}")
        m2m_fields = {"tags_ids": "tags_ids"}
        processed_m2m_fields = {}
        for field in m2m_fields:
            processed_m2m_fields[field] = [item[1] for item in vals.get(field, [])]
        dynamic_fields = {
            "is_company": False,
            "is_group": active_record.is_group,
            "is_registrant": True,
            "db_import": "yes",
            **processed_m2m_fields,
        }
        static_fields = self.get_fields_in_view()
        draft_record = {}
        draft_record.update(dynamic_fields)
        self._update_fields_from_vals(draft_record, vals)
        self._update_fields_from_static(draft_record, static_fields, vals, registrant_data, model_name)
        if not self.is_group and (vals.get("given_name") or vals.get("family_name") or vals.get("addl_name")):
            draft_record["name"] = self._compose_name(vals)
        active_record.write({"registrant_data": json.dumps(draft_record)})
        if active_record.is_group:
            member_ids = self._extract_member_ids_from_commands(vals.get("draft_member_ids"))
            if member_ids:
                unique_ids = sorted(set(member_ids))
                active_record.write(
                    {"draft_member_ids": [(6, 0, unique_ids)], "group_member_ids_json": unique_ids}
                )
        self._sync_direct_fields(active_record, vals)
        change_requests = self.env["g2p.change.request"].search([("draft_record_id", "=", active_record.id)])
        if change_requests:
            for cr in change_requests:
                cr._update_change_request_name()

    def _update_fields_from_vals(self, draft_record, vals):
        for field_name, field_value in vals.items():
            if field_name not in draft_record:
                draft_record[field_name] = field_value

    def _update_fields_from_static(self, draft_record, static_fields, vals, registrant_data, model_name):
        for field in static_fields:
            if field in self.env[model_name]._fields:
                draft_record[field] = vals.get(field, registrant_data.get(field))
            else:
                if field in vals:
                    draft_record[field] = vals[field]

    def _compose_name(self, vals):
        name_parts = [
            val.upper()
            for val in [vals.get("given_name"), vals.get("family_name"), vals.get("addl_name")]
            if val
        ]
        return " ".join(filter(None, name_parts)).strip()

    def _extract_member_ids_from_commands(self, cmds):
        member_ids = []
        if isinstance(cmds, list):
            for cmd in cmds:
                if isinstance(cmd, list | tuple) and len(cmd) >= 2:
                    if cmd[0] == 6 and len(cmd) >= 3 and isinstance(cmd[2], list):
                        member_ids.extend(int(x) for x in cmd[2])
                    elif cmd[0] == 4 and isinstance(cmd[1], int):
                        member_ids.append(int(cmd[1]))
                    elif cmd[0] == 3 and isinstance(cmd[1], int):
                        try:
                            member_ids.remove(int(cmd[1]))
                        except ValueError as e:
                            _logger.warning(
                                f"Tried to remove draft_member_id \
                                {cmd[1]} but it was not present: {e}"
                            )
        return member_ids

    def _sync_direct_fields(self, active_record, vals):
        direct_fields = ["region", "name", "given_name", "family_name", "addl_name", "gender", "phone"]
        update_vals = {}
        for field in direct_fields:
            field_val = vals.get(field)
            if field_val and hasattr(active_record, field):
                if field == "region":
                    region = self.env["g2p.region"].browse(field_val)
                    update_vals[field] = region.name if region.exists() else ""
                else:
                    update_vals[field] = field_val
        if update_vals:
            active_record.write(update_vals)

    def action_publish(self):
        context = self.env.context
        model_name = context.get("active_model")
        record_id = context.get("active_id")
        record = self.env[model_name].browse(record_id)
        record.action_publish()

    def action_submit(self):
        context = self.env.context
        model_name = context.get("active_model")
        record_id = context.get("active_id")
        record = self.env[model_name].browse(record_id)
        record.action_submit()

    def get_fields_in_view(self):
        views = self.env["ir.ui.view"].search(
            [
                ("model", "=", "res.partner"),
                ("type", "=", "form"),  # Assuming you want to get fields from form view
            ]
        )

        # Initialize a set to store field names from all views (base and inherited)
        fields_in_view = set()

        # Loop through each view (including inherited ones)
        for view in views:
            # Get the architecture of the view
            arch = view.arch

            # Use lxml to parse the XML
            root = etree.fromstring(arch)

            # Loop through all the <field> tags and collect the field names
            for field in root.xpath("//field"):
                field_name = field.get("name")
                if field_name:
                    fields_in_view.add(field_name)

        # Now compare fields_in_view with actual fields in the model
        all_fields_in_model = set(self._fields.keys())
        usable_fields = all_fields_in_model.intersection(fields_in_view)

        return usable_fields

    def write(self, vals):
        """Override write to update change request names when draft record is updated."""
        result = super().write(vals)

        # Update change request names if draft record name changed
        if "name" in vals:
            change_requests = self.env["g2p.change.request"].search([("draft_record_id", "in", self.ids)])
            if change_requests:
                change_requests.update_name_from_registrant()

        return result
