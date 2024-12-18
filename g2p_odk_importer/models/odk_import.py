import logging
import traceback
from datetime import datetime, timedelta

import jq

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .odk_client import ODKClient

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

    enable_import_instance = fields.Char(string="ODK Setting Param", compute="_compute_config_param_value")

    @api.depends()
    def _compute_config_param_value(self):
        config_value = self.env["ir.config_parameter"].sudo().get_param("g2p_odk_importer.enable_odk")
        for record in self:
            record.enable_import_instance = config_value

    # ********** Fetch record using instance ID ************
    instance_id = fields.Char()

    def fetch_record_by_instance_id(self):
        ODK_SETTING = self.env["ir.config_parameter"].get_param("g2p_odk_importer.enable_odk")
        if not ODK_SETTING:
            raise UserError(_("Please enable the ODK import instanceID in the ResConfig settings"))

        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))

        if not self.instance_id:
            raise UserError(_("Please give the instance ID."))

        for config in self:
            client = ODKClient(
                self.env,
                config.id,
                config.odk_config.base_url,
                config.odk_config.username,
                config.odk_config.password,
                config.odk_config.project,
                config.odk_config.form_id,
                config.target_registry,
                config.json_formatter,
            )
            client.login()
            imported = client.import_record_by_instance_id(
                instance_id=config.instance_id, last_sync_timestamp=config.last_sync_time
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
        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))
        for config in self:
            client = ODKClient(
                self.env,
                config.id,
                config.odk_config.base_url,
                config.odk_config.username,
                config.odk_config.password,
                config.odk_config.project,
                config.odk_config.form_id,
                config.target_registry,
            )
            client.login()
            test = client.test_connection()
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
        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))

        enable_odk_async = self.env["ir.config_parameter"].get_param("g2p_odk_importer.enable_odk_async")

        for config in self:
            client = ODKClient(
                self.env,
                config.id,
                config.odk_config.base_url,
                config.odk_config.username,
                config.odk_config.password,
                config.odk_config.project,
                config.odk_config.form_id,
                config.target_registry,
                config.json_formatter,
            )
            client.login()
            if enable_odk_async:
                instance_ids = client.get_submissions(fields="__id", last_sync_time=config.last_sync_time)
                # Store instance IDs in the database
                for instance_id in instance_ids:
                    if isinstance(instance_id, dict):
                        meta = instance_id.get("meta", {})
                        extracted_instance_id = meta.get("instanceID")
                    if isinstance(instance_id, dict):
                        # Extract the instance ID from the 'meta' field
                        meta = instance_id.get("meta", {})
                        extracted_instance_id = meta.get("instanceID")

                        if extracted_instance_id:
                            self.env["odk.instance.id"].create(
                                {
                                    "instance_id": extracted_instance_id,
                                    "odk_import_id": config.id,
                                    "status": "pending",
                                }
                            )
                        else:
                            _logger.error(f"'meta' field missing 'instanceID': {instance_id}")

                config.update({"last_sync_time": fields.Datetime.now()})
                self.process_pending_instances()
            else:
                imported = client.import_delta_records(last_sync_timestamp=config.last_sync_time)
                if "form_updated" in imported:
                    partner_count = imported.get("partner_count", 0)
                    message = f"ODK form {partner_count} records were imported successfully."
                    types = "success"
                    config.update({"last_sync_time": fields.Datetime.now()})
                elif "form_failed" in imported:
                    message = "ODK form import failed"
                    types = "danger"
                else:
                    message = "No new form records were submitted."
                    types = "warning"
                    config.update({"last_sync_time": fields.Datetime.now()})
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
        for rec in self:
            if rec.job_status == "draft" or rec.job_status == "completed":
                _logger.info("Job Started")
                rec.job_status = "started"
                ir_cron = self.env["ir.cron"].sudo()
                rec.cron_id = ir_cron.create(
                    {
                        "name": "ODK Pull Cron " + rec.odk_config.name + " #" + str(rec.id),
                        "active": True,
                        "interval_number": rec.interval_hours,
                        "interval_type": "minutes",
                        "model_id": self.env["ir.model"].search([("model", "=", "odk.import")]).id,
                        "state": "code",
                        "code": "model.browse(" + str(rec.id) + ").import_records()",
                        "doall": False,
                        "numbercall": -1,
                    }
                )
                rec.job_status = "running"
                now_datetime = datetime.now()
                rec.update(
                    {
                        "start_datetime": now_datetime - timedelta(hours=rec.interval_hours),
                        "end_datetime": now_datetime,
                    }
                )

            elif rec.job_status == "started" or rec.job_status == "running":
                _logger.info("Job Stopped")
                rec.job_status = "completed"
                rec.sudo().cron_id.unlink()
                rec.cron_id = None

    def process_pending_instances(self):
        _logger.info("Processing the ODK Async using Job Queue")
        batch_size = 10  # Define the batch size as per your requirement
        pending_instance_ids = self.env["odk.instance.id"].search([("status", "=", "pending")])
        if not pending_instance_ids:
            _logger.info("No pending instance IDs found.")
            return

        _logger.info(f"Found {len(pending_instance_ids)} pending instance IDs.")

        for batch_start in range(0, len(pending_instance_ids), batch_size):
            batch = pending_instance_ids[batch_start : batch_start + batch_size]
            _logger.info(f"Submitting batch of {len(batch)} instance IDs.")
            self.with_delay()._process_instance_id(batch)

    def _process_instance_id(self, instance_ids):
        for instance_id in instance_ids:
            _logger.info("Processing instance ID", instance_id.instance_id)
            instance_id.sudo().status = "processing"
            client = ODKClient(
                self.env,
                instance_id.odk_import_id.id,
                instance_id.odk_import_id.odk_config.base_url,
                instance_id.odk_import_id.odk_config.username,
                instance_id.odk_import_id.odk_config.password,
                instance_id.odk_import_id.odk_config.project,
                instance_id.odk_import_id.odk_config.form_id,
                instance_id.odk_import_id.target_registry,
                instance_id.odk_import_id.json_formatter,
            )
            client.login()
            try:
                client.import_record_by_instance_id(instance_id.instance_id)
                instance_id.sudo().write({"status": "processing"})
            except Exception as exc:
                _logger.error(traceback.format_exc())
                _logger.error(f"Failed to import instance ID {instance_id.instance_id}: {exc}")
                instance_id.sudo().write({"status": "failed"})
