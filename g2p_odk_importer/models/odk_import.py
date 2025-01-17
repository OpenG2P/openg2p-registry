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

    # ********** Fetch record using instance ID ************
    instance_id = fields.Char()

    def fetch_record_by_instance_id(self):
        self.ensure_one()
        if not self.enable_import_by_instance_id:
            raise UserError(_("Please enable the ODK import instanceID"))

        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))

        if not self.instance_id:
            raise UserError(_("Please give the instance ID."))

        imported = self.odk_config.import_records(
            self.json_formatter,
            self.target_registry,
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

    def import_records(self):
        self.ensure_one()
        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))

        if self.enable_async:
            instance_ids = self.odk_config.get_submissions(fields="__id", last_sync_time=self.last_sync_time)
            for instance in instance_ids:
                if isinstance(instance, dict):
                    # Extract the '__id' directly
                    extracted_instance_id = instance.get("__id")

                    if extracted_instance_id:
                        # Create a record in the 'odk.instance.id' model
                        self.env["odk.instance.id"].create(
                            {
                                "instance_id": extracted_instance_id,
                                "odk_import_id": self.id,
                                "status": "pending",
                            }
                        )
                    else:
                        # Log an error if '__id' is missing
                        _logger.error(f"Missing '__id' in submission: {instance}")

            self.last_sync_time = fields.Datetime.now()
            return self.process_pending_instances()
        else:
            imported = self.odk_config.import_records(
                self.json_formatter, self.target_registry, last_sync_time=self.last_sync_time
            )
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
        self.ensure_one()
        if self.job_status == "draft" or self.job_status == "completed":
            _logger.info("Job Started")
            self.job_status = "started"
            IR_CRON = self.env["ir.cron"].sudo()
            self.cron_id = IR_CRON.create(
                {
                    "name": "ODK Pull Cron " + self.odk_config.name + " #" + str(self.id),
                    "active": True,
                    "interval_number": self.interval_hours,
                    "interval_type": "minutes",
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

    @api.model
    def process_pending_instances(self):
        _logger.info("Processing the ODK Async using Job Queue")
        batch_size = 10  # Define the batch size as per your requirement
        pending_instance_ids = self.env["odk.instance.id"].sudo().search([("status", "=", "pending")])
        if not pending_instance_ids:
            _logger.info("No pending instance IDs found.")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "warning",
                    "message": "No pending instance IDs found to process.",
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }

        total_instances = len(pending_instance_ids)
        _logger.info(f"Found {total_instances} pending instance IDs.")

        for batch_start in range(0, len(pending_instance_ids), batch_size):
            batch = pending_instance_ids[batch_start : batch_start + batch_size]
            _logger.info(f"Submitting batch of {len(batch)} instance IDs.")
            self.with_delay()._process_instance_id(batch)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": f"Started the import process for {total_instances} registrants in batches.",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    @api.model
    def _process_instance_id(self, instance_ids):
        for instance in instance_ids:
            _logger.info("Processing instance ID: %s", instance.instance_id)
            instance.status = "processing"
            try:
                instance.odk_import_id.odk_config.import_records(
                    self.json_formatter, self.target_registry, instance_id=instance.instance_id
                )
                instance.write({"status": "processing"})
            except Exception as exc:
                _logger.error(traceback.format_exc())
                _logger.error(f"Failed to import instance ID {instance.instance_id}: {exc}")
                instance.status = "failed"
