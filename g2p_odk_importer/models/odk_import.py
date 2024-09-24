import logging
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

    def import_records_by_cron(self, _id):
        config = self.env["odk.config"].browse(_id)
        if not config.base_url:
            raise UserError(_("Please configure the ODK."))
        client = ODKClient(
            self.env,
            config.id,
            config.base_url,
            config.username,
            config.password,
            config.project,
            config.form_id,
            self.target_registry,
            self.json_formatter,
        )
        client.login()
        client.import_delta_records(last_sync_timestamp=config.last_sync_time)
        config.update({"last_sync_time": fields.Datetime.now()})

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
                        "code": "model.import_records_by_cron(" + str(rec.id) + ")",
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
