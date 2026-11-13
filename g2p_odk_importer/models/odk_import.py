import base64
import logging
import traceback
from datetime import datetime, timedelta

import jq

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OdkImport(models.Model):
    _name = "odk.import"
    _description = "ODK Import"

    # Dedicated queue_job channel (configure capacity via queue_job.channels, e.g. root.odk_import:2).
    ODK_IMPORT_JOB_CHANNEL = "root.odk_import"

    odk_config = fields.Many2one("odk.config", string="ODK Config", required=True)
    odk_config_name = fields.Char(related="odk_config.name")
    json_formatter = fields.Text(string="JSON Formatter", required=True)
    target_registry = fields.Selection([("individual", "Individual"), ("group", "Group")], required=True)
    last_sync_time = fields.Datetime(string="Last synced on", required=False)
    cron_id = fields.Many2one("ir.cron", string="Cron Job", required=False)
    job_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("started", "Started"),
            ("running", "Running"),
            ("completed", "Completed"),
        ],
        string="Status",
        required=True,
        default="draft",
    )

    interval_hours = fields.Integer(string="Interval in hours", required=False)
    start_datetime = fields.Datetime(string="Start Time", required=False)
    end_datetime = fields.Datetime(string="End Time", required=False)

    enable_import_by_instance_id = fields.Boolean()
    enable_async = fields.Boolean()
    # Cap how many pending rows one cron tick claims/enqueues (avoids flooding queue_job).
    async_claim_limit = fields.Integer(
        string="Async Claim Limit",
        default=500,
        help="Max pending instance IDs to claim and enqueue per import run. "
        "Remaining pending rows are picked up on the next cron/import.",
    )
    # Instances processed per queue_job job.
    async_batch_size = fields.Integer(
        string="Async Batch Size",
        default=10,
        help="How many ODK instance IDs each queue job processes.",
    )

    # ********** Fetch record using instance ID ************
    instance_id = fields.Char()

    def fetch_record_by_instance_id(self):
        """This method is run when 'Fetch Record by Instance Id' button is clicked on UI."""
        self.ensure_one()
        if not self.enable_import_by_instance_id:
            raise UserError(_("Please enable the ODK import instanceID"))

        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))

        if not self.instance_id:
            raise UserError(_("Please give the instance ID."))

        imported = self.process_records(
            instance_id=self.instance_id,
            last_sync_time=self.last_sync_time,
        )
        if "form_updated" in imported:
            message = "ODK form records is imported successfully."
            types = "success"
        elif "form_failed" in imported:
            message = "ODK form import failed"
            types = "danger"
        else:
            message = "No record found using this instance ID."
            types = "warning"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": types,
                "message": message,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    # ******************  END  ***************************

    @api.constrains("json_formatter")
    def constraint_json_fields(self):
        for rec in self:
            if rec.json_formatter:
                try:
                    jq.compile(rec.json_formatter)
                except ValueError as ve:
                    raise ValidationError(_("Json Format is not valid jq expression.")) from ve

    def test_connection(self):
        self.ensure_one()
        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))
        test = self.odk_config.test_connection()
        if test:
            message = "Tested successfully."
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": message,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _register_odk_instance(self, extracted_instance_id):
        """Create a pending odk.instance.id row if this instance was never seen.

        Returns True if a new row was created, False if it already existed.
        Unique SQL constraint + pre-check prevent duplicate workers on re-pull.
        Delete the instance row in the UI to allow intentional re-import.
        """
        self.ensure_one()
        Instance = self.env["odk.instance.id"].sudo()
        existing = Instance.search([("instance_id", "=", extracted_instance_id)], limit=1)
        if existing:
            _logger.debug(
                "Skipping already-registered ODK instance %s (status=%s)",
                extracted_instance_id,
                existing.status,
            )
            return False
        Instance.create(
            {
                "instance_id": extracted_instance_id,
                "odk_import_id": self.id,
                "status": "pending",
            }
        )
        return True

    def import_records(self):
        """
        This method runs inside the cron job that is created when button is clicked.
        """
        self.ensure_one()

        if self.enable_async:
            instance_ids = self.odk_config.get_submissions(fields="__id", last_sync_time=self.last_sync_time)
            new_count = 0
            for instance in instance_ids:
                if not isinstance(instance, dict):
                    continue
                extracted_instance_id = instance.get("__id")
                if not extracted_instance_id:
                    _logger.error("Missing '__id' in submission: %s", instance)
                    continue
                if self._register_odk_instance(extracted_instance_id):
                    new_count += 1

            # Advance watermark only after instance rows are persisted.
            # Unique(instance_id) prevents duplicate rows if the same
            # submissions are pulled again; delete a row to re-import.
            self.last_sync_time = fields.Datetime.now()
            _logger.info(
                "ODK import %s: registered %s new instance(s); advancing last_sync_time",
                self.id,
                new_count,
            )
            return self.process_pending_instances()
        else:
            imported = self.process_records(last_sync_time=self.last_sync_time)
            if "form_updated" in imported:
                partner_count = imported.get("partner_count", 0)
                message = f"ODK form {partner_count} records were imported successfully."
                types = "success"
                self.last_sync_time = fields.Datetime.now()
            elif "form_failed" in imported:
                message = "ODK form import failed"
                types = "danger"
            else:
                message = "No new form records were submitted."
                types = "warning"
                self.last_sync_time = fields.Datetime.now()
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": types,
                    "message": message,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }

    def odk_import_action_trigger(self):
        """This method is called when 'Import Records' button is clicked on UI."""
        self.ensure_one()
        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))
        if self.job_status == "draft" or self.job_status == "completed":
            _logger.info("Job Started")
            self.job_status = "started"
            IR_CRON = self.env["ir.cron"].sudo()
            self.cron_id = IR_CRON.create(
                {
                    "name": "ODK Pull Cron " + self.odk_config.name + " #" + str(self.id),
                    "active": True,
                    "interval_number": self.interval_hours,
                    "interval_type": "hours",
                    "model_id": self.env["ir.model"].search([("model", "=", "odk.import")]).id,
                    "state": "code",
                    "code": f"model.browse({self.id}).import_records()",
                    "doall": False,
                    "numbercall": -1,
                }
            )
            self.job_status = "running"
            now_datetime = datetime.now()
            self.write(
                {
                    "start_datetime": now_datetime - timedelta(hours=self.interval_hours),
                    "end_datetime": now_datetime,
                }
            )

        elif self.job_status == "started" or self.job_status == "running":
            _logger.info("Job Stopped")
            self.sudo().cron_id.unlink()
            self.write({"job_status": "completed", "cron_id": None})

    def process_pending_instances(self):
        """Claim a limited set of pending instances and enqueue queue_job batches."""
        self.ensure_one()
        _logger.info("Processing the ODK Async using Job Queue for import %s", self.id)
        batch_size = max(1, self.async_batch_size or 10)
        claim_limit = max(batch_size, self.async_claim_limit or 500)
        pending_instance_ids = (
            self.env["odk.instance.id"]
            .sudo()
            .search(
                [
                    ("status", "=", "pending"),
                    ("odk_import_id", "=", self.id),
                ],
                order="id asc",
                limit=claim_limit,
            )
        )
        if not pending_instance_ids:
            _logger.info("No pending instance IDs found for import %s.", self.id)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "warning",
                    "message": "No pending instance IDs found to process.",
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }

        # Claim before enqueue so the next cron cannot re-queue the same rows.
        pending_instance_ids.write({"status": "queued"})

        total_instances = len(pending_instance_ids)
        remaining = (
            self.env["odk.instance.id"]
            .sudo()
            .search_count(
                [
                    ("status", "=", "pending"),
                    ("odk_import_id", "=", self.id),
                ]
            )
        )
        _logger.info(
            "Claimed %s pending instance IDs for import %s (batch_size=%s, %s still pending).",
            total_instances,
            self.id,
            batch_size,
            remaining,
        )

        import_label = self.odk_config_name or self.odk_config.name or ("Import #%s" % self.id)
        for batch_start in range(0, len(pending_instance_ids), batch_size):
            batch = pending_instance_ids[batch_start : batch_start + batch_size]
            batch_ids = batch.ids
            batch_end = batch_start + len(batch_ids)
            identity_key = "odk.import.%s.batch.%s-%s" % (
                self.id,
                batch_ids[0],
                batch_ids[-1],
            )
            description = _(
                "ODK Import '%(import)s' (#%(import_id)s): process %(count)s instance(s) "
                "[batch %(from)s-%(to)s of %(total)s]"
            ) % {
                "import": import_label,
                "import_id": self.id,
                "count": len(batch_ids),
                "from": batch_start + 1,
                "to": batch_end,
                "total": total_instances,
            }
            _logger.info(
                "Submitting batch of %s instance IDs (identity_key=%s, channel=%s).",
                len(batch_ids),
                identity_key,
                self.ODK_IMPORT_JOB_CHANNEL,
            )
            self.with_delay(
                identity_key=identity_key,
                description=description,
                channel=self.ODK_IMPORT_JOB_CHANNEL,
            )._process_pending_instance_id(batch_ids)

        message = f"Started the import process for {total_instances} registrants in batches."
        if remaining:
            message += f" {remaining} pending left for the next run."
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": message,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _count_partners_created_in_current_tx(self):
        """Count res.partner rows inserted in *this* DB transaction only.

        Safe with parallel queue jobs: other workers commit under different
        transaction IDs, so a global search_count before/after would race.

        PostgreSQL 16+: txid_current() is bigint and cannot CAST to xid, so
        compare via the low 32 bits of the epoch-extended transaction id.
        """
        self.env["res.partner"].flush_model()
        self.env.cr.execute(
            """
            SELECT COUNT(*)
              FROM res_partner
             WHERE xmin::text::bigint = txid_current() % (2^32)::bigint
            """
        )
        return self.env.cr.fetchone()[0]

    @api.model
    def _process_pending_instance_id(self, instance_ids):
        """ODK Import: process a batch of pending instance IDs."""
        instances = self.env["odk.instance.id"].sudo().browse(instance_ids).exists()
        for instance in instances:
            _logger.info("Processing instance ID: %s", instance.instance_id)
            instance.set_status("processing")
            try:
                result = instance.odk_import_id.process_records(instance_id=instance.instance_id)
                errors = result.get("errors") or [] if isinstance(result, dict) else []
                partner_count = (result or {}).get("partner_count", 0) if isinstance(result, dict) else 0
                if errors and partner_count > 0:
                    instance.set_status("partial", error_message="\n".join(errors))
                elif errors:
                    instance.set_status("failed", error_message="\n".join(errors))
                else:
                    instance.set_status("done")
            except Exception as exc:
                _logger.error(traceback.format_exc())
                _logger.error("Failed to import instance ID %s: %s", instance.instance_id, exc)
                err_msg = str(exc)
                # Partner rows flushed in this job's transaction only (not other workers).
                try:
                    created_in_tx = instance.odk_import_id._count_partners_created_in_current_tx()
                except Exception:
                    _logger.exception(
                        "Could not detect partners created in current tx for %s; "
                        "marking as failed",
                        instance.instance_id,
                    )
                    created_in_tx = 0
                if created_in_tx:
                    instance.set_status("partial", error_message=err_msg)
                else:
                    instance.set_status("failed", error_message=err_msg)

    def process_records(self, instance_id=None, last_sync_time=None):
        """This is a generic process_records api called by various above methods for importing records."""
        self.ensure_one()

        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))

        data = self.odk_config.download_records(instance_id=instance_id, last_sync_time=last_sync_time)

        partner_count = 0
        for member in data["value"]:
            _logger.debug("ODK RAW DATA:%s" % member)

            mapped_json = jq.first(self.json_formatter, member)
            if self.target_registry == "individual":
                mapped_json.update({"is_registrant": True, "is_group": False})
            elif self.target_registry == "group":
                mapped_json.update({"is_registrant": True, "is_group": True})

            self.process_records_handle_enumerator_info(mapped_json, member)
            self.process_records_handle_one2many_fields(mapped_json, member)
            self.process_records_handle_media_import(mapped_json, member)
            self.process_records_handle_many2one_fields(mapped_json)
            self.process_records_handle_addl_data(mapped_json)

            self.env["res.partner"].sudo().create(mapped_json)
            partner_count += 1
            data.update({"form_updated": True})

        data.update({"partner_count": partner_count})

        return data

    def create_enumerator(self, member):
        """Creates an enumerator record from ODK member data."""
        system_data = member.get("__system", {})
        submitter_name = str(system_data.get("submitterName"))
        submitter_id = str(system_data.get("submitterId"))
        submission_date_str = system_data.get("submissionDate")
        submission_date = datetime.strptime(submission_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()

        enumerator = self.env["g2p.enumerator"].create(
            {
                "name": submitter_name,
                "enumerator_user_id": submitter_id,
                "data_collection_date": submission_date,
            }
        )
        return enumerator

    def process_records_handle_enumerator_info(self, mapped_json, member):
        """Processes records from ODK and assigns odk_app_user_id"""
        enumerator = self.create_enumerator(member)
        mapped_json["enumerator_id"] = enumerator.id
        return enumerator

    def process_records_handle_many2one_fields(self, mapped_json):
        self.ensure_one()
        if self.target_registry == "group" and "kind" in mapped_json:
            kind_name = mapped_json.get("kind")
            if kind_name:
                kind_record = self.env["g2p.group.kind"].search([("name", "=", kind_name)], limit=1)
                if kind_record:
                    mapped_json["kind"] = kind_record.id

    def process_records_handle_one2many_fields(self, mapped_json, member):
        self.ensure_one()
        if "phone_number_ids" in mapped_json:
            mapped_json["phone_number_ids"] = [
                (
                    0,
                    0,
                    {
                        "phone_no": phone.get("phone_no"),
                        "date_collected": phone.get("date_collected"),
                        "disabled": phone.get("disabled"),
                    },
                )
                for phone in mapped_json["phone_number_ids"]
            ]

        if "group_membership_ids" in mapped_json and self.target_registry == "group":
            individual_ids = []
            relationships_ids = []
            group_membership_data = (
                mapped_json.get("group_membership_ids")
                if mapped_json.get("group_membership_ids") is not None
                else []
            )

            for individual_mem in group_membership_data:
                individual_data = self.get_individual_data(individual_mem)

                self.get_enumerator_info(member, individual_data)

                individual = self.env["res.partner"].sudo().create(individual_data)
                if individual:
                    kind = self.get_member_kind(individual_mem)
                    individual_data = {"individual": individual.id}
                    if kind:
                        individual_data["kind"] = [(4, kind.id)]
                    relationship = self.get_member_relationship(individual.id, individual_mem)
                    if relationship:
                        relationships_ids.append((0, 0, relationship))
                    individual_ids.append((0, 0, individual_data))
            mapped_json["related_1_ids"] = relationships_ids
            mapped_json["group_membership_ids"] = individual_ids

        if "reg_ids" in mapped_json:
            reg_ids = mapped_json["reg_ids"]
            mapped_json["reg_ids"] = []
            for reg_id in reg_ids:
                id_type = self.env["g2p.id.type"].search([("name", "=", reg_id.get("id_type"))], limit=1)
                if not id_type:
                    raise ValidationError(
                        f"ID Type not found while handling Reg IDs. {reg_id.get('id_type')}"
                    )
                mapped_json["reg_ids"].append(
                    (
                        0,
                        0,
                        {
                            "id_type": id_type.id,
                            "value": reg_id.get("value"),
                            "expiry_date": reg_id.get("expiry_date"),
                            "status": reg_id.get("status"),
                        },
                    )
                )

    def process_records_handle_media_import(self, mapped_json, member):
        self.ensure_one()
        instance_id = member.get("meta", {}).get("instanceID")
        if not instance_id:
            return
        if mapped_json.get("image_1920", None):
            attachm = self.odk_config.download_attachment(instance_id, mapped_json["image_1920"])
            if attachm:
                mapped_json["image_1920"] = base64.b64encode(attachm).decode("utf-8")

    def process_records_handle_addl_data(self, mapped_json):
        # Override this method to add more data
        return mapped_json

    def get_enumerator_info(self, member, individual_data):
        """Assigns odk_app_user_id and enumerator details for group members."""
        enumerator = self.create_enumerator(member)
        individual_data.update(
            {
                "enumerator_id": enumerator.id,
            }
        )
        return enumerator

    def get_member_kind(self, record):
        kind_as_str = record.get("kind", None)
        if kind_as_str:
            return self.env["g2p.group.membership.kind"].search([("name", "=", kind_as_str)], limit=1)
        return None

    def get_member_relationship(self, source_id, record):
        member_relation = record.get("relationship_with_head", None)
        if member_relation:
            relation = self.env["g2p.relationship"].search([("name", "=", member_relation)], limit=1)

            if relation:
                return {"source": source_id, "relation": relation.id, "start_date": datetime.now()}

        _logger.warning("No relation defined for member")

        return None

    def get_individual_data(self, record):
        name = record.get("name", None)
        if name is not None:
            given_name = name.split(" ")[0]
            family_name = name.split(" ")[-1]
            addl_name = " ".join(name.split(" ")[1:-1])
        else:
            given_name = None
            family_name = None
            addl_name = None
        dob = self.get_dob(record)
        gender = self.get_gender(record.get("gender"))

        return {
            "name": name,
            "given_name": given_name,
            "family_name": family_name,
            "addl_name": addl_name,
            "is_registrant": True,
            "is_group": False,
            "birthdate": dob,
            "gender": gender,
        }

    def get_gender(self, gender_val):
        if gender_val:
            gender = self.env["gender.type"].sudo().search([("value", "=", gender_val)], limit=1)
            return gender.code if gender else None
        return None

    def get_dob(self, record):
        dob = record.get("birthdate")
        if dob:
            return dob

        age = record.get("age")
        if age:
            now = datetime.now()
            birth_year = now.year - age
            if birth_year < 0:
                _logger.warning("Future birthdate is not allowed.")
                return None
            return now.replace(year=birth_year).strftime("%Y-%m-%d")
        return None
