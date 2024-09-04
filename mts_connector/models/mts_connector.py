import json
import logging
from datetime import datetime, timedelta

import pyjq
import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MTSConnector(models.Model):
    _name = "mts.connector"
    _description = "Mosip Token Seeder Connectors"

    name = fields.Char(required=True)
    # only odk input, json output, and callback deliverytype supported as of now
    mts_url = fields.Char(
        string="URL to reach MTS",
        required=True,
        default="http://mosip-token-seeder.mosip-token-seeder",
    )
    input_type = fields.Selection(
        [("odk", "ODK"), ("custom", "Custom")], string="MTS Input Type", required=True
    )
    mapping = fields.Text(
        required=True,
        default="""{
            "vid": "vid",
            "name": ["name"],
            "gender": "gender",
            "dob": "dob",
            "phoneNumber": "phoneNumber",
            "emailId": "emailId",
            "fullAddress": ["fullAddress"]
            }""",
    )
    output_type = fields.Selection([("json", "JSON")], string="MTS Output Type", required=True)
    output_format = fields.Text(string="MTS Output Format", required=False)
    delivery_type = fields.Selection([("callback", "Callback")], string="MTS Delivery Type", required=True)
    lang_code = fields.Char(string="Mosip Language", required=True, default="eng")
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

    # Job Configurations
    is_recurring = fields.Selection(
        [("recurring", "Recurring"), ("onetime", "One time")],
        string="Job Type",
        required=True,
    )
    cron_id = fields.Many2one(
        "ir.cron",
        string="Cron Job",
        help="linked to this MTS configuration",
        required=False,
    )
    start_datetime = fields.Datetime(string="Start Time", required=False)
    end_datetime = fields.Datetime(string="End Time", required=False)
    interval_minutes = fields.Integer(string="Interval in minutes", required=False)

    # odk configurations
    odk_base_url = fields.Char(string="ODK Base Url", required=False)
    odk_odata_url = fields.Char(string="ODK ODATA Url", required=False)
    odk_email = fields.Char(string="ODK User email", required=False)
    odk_password = fields.Char(string="ODK User password", required=False)

    # callback configurations
    callback_url = fields.Char(string="Callback URL", required=False)
    callback_httpmethod = fields.Selection(
        [("POST", "POST"), ("PUT", "PUT"), ("GET", "GET"), ("PATCH", "PATCH")],
        string="Callback HTTP Method",
        required=False,
    )
    callback_timeout = fields.Integer(required=False, default=10)
    callback_authtype = fields.Selection([("odoo", "Odoo")], string="Callback Auth Type", required=False)
    callback_auth_url = fields.Char(required=False)
    callback_auth_database = fields.Char(required=False)
    callback_auth_username = fields.Char(required=False)
    callback_auth_password = fields.Char(required=False)

    @api.constrains("start_datetime")
    def constraint_start_date(self):
        for rec in self:
            if rec.start_datetime:
                if rec.start_datetime > datetime.now():
                    raise ValidationError(_("Start Time cannot be after the current time."))

    @api.constrains("end_datetime")
    def constraint_end_date(self):
        for rec in self:
            if rec.end_datetime:
                if rec.end_datetime > datetime.now():
                    raise ValidationError(_("End Time cannot be after the current time."))
                if rec.end_datetime < rec.start_datetime:
                    raise ValidationError(_("End Time cannot be after Start Time."))

    @api.constrains("mapping", "output_format")
    def constraint_json_fields(self):
        for rec in self:
            if rec.mapping:
                try:
                    json.loads(rec.mapping)
                except ValueError as ve:
                    raise ValidationError(_("Mapping is not valid json.")) from ve
            if rec.output_format:
                try:
                    pyjq.compile(rec.output_format)
                except ValueError as ve:
                    raise ValidationError(_("Output Format is not valid jq expression.")) from ve

    def mts_action_trigger(self):
        for rec in self:
            if rec.job_status == "draft" or rec.job_status == "completed":
                _logger.info("Job Started")
                rec.job_status = "started"
                if rec.is_recurring == "recurring":
                    ir_cron = self.env["ir.cron"].sudo()
                    rec.cron_id = ir_cron.create(
                        {
                            "name": "MTS Cron " + rec.name + " #" + str(rec.id),
                            "active": True,
                            "interval_number": rec.interval_minutes,
                            "interval_type": "minutes",
                            "model_id": self.env["ir.model"].search([("model", "=", "mts.connector")]).id,
                            "state": "code",
                            "code": "model.mts_onetime_action(" + str(rec.id) + ")",
                            "doall": False,
                            "numbercall": -1,
                        }
                    )
                    rec.job_status = "running"
                    now_datetime = datetime.now()
                    rec.update(
                        {
                            "start_datetime": now_datetime - timedelta(minutes=rec.interval_minutes),
                            "end_datetime": now_datetime,
                        }
                    )
                elif rec.is_recurring == "onetime":
                    self.with_delay().mts_onetime_action(rec.id)
                    _logger.info("Initialized one time " + str(rec.id))
            elif rec.job_status == "started" or rec.job_status == "running":
                _logger.info("Job Stopped")
                rec.job_status = "completed"
                if rec.is_recurring == "recurring":
                    rec.sudo().cron_id.unlink()
                    rec.cron_id = None

    def mts_onetime_action(self, _id: int):
        _logger.info("Being called everytime. Id: " + str(_id))
        current_conf: MTSConnector = self.env["mts.connector"].browse(_id)
        # execute here
        dt_now = datetime.utcnow()
        mts_request = {
            "id": "string",
            "version": "string",
            "metadata": "string",
            "requesttime": self.datetime_to_iso(dt_now),
            "request": {
                "output": current_conf.output_type,
                "deliverytype": current_conf.delivery_type,
                "mapping": json.loads(current_conf.mapping),
                "lang": current_conf.lang_code,
                "outputFormat": current_conf.output_format,
            },
        }
        if current_conf.delivery_type == "callback":
            mts_request["request"]["callbackProperties"] = {
                "url": current_conf.callback_url,
                "httpMethod": current_conf.callback_httpmethod,
                "timeoutSeconds": current_conf.callback_timeout,
                "callInBulk": False,
                "authType": current_conf.callback_authtype,
            }
            if current_conf.callback_authtype == "odoo":
                mts_request["request"]["callbackProperties"]["authOdoo"] = {
                    "database": current_conf.callback_auth_database,
                    "authUrl": current_conf.callback_auth_url,
                    "username": current_conf.callback_auth_username,
                    "password": current_conf.callback_auth_password,
                }
        if current_conf.input_type == "odk":
            mts_request["request"]["odkconfig"] = {
                "baseurl": current_conf.odk_base_url,
                "odataurl": current_conf.odk_odata_url,
                "projectid": "",
                "formid": "",
                "email": current_conf.odk_email,
                "password": current_conf.odk_password,
                "startdate": self.datetime_to_iso(current_conf.end_datetime),
                "enddate": self.datetime_to_iso(dt_now),
            }
        if current_conf.input_type == "custom":
            current_conf.custom_single_action(mts_request)
            return
        _logger.info("Request to MTS %s", json.dumps(mts_request))
        mts_res = requests.post(
            f"{current_conf.mts_url}/authtoken/{current_conf.input_type}",
            json=mts_request,
            timeout=current_conf.callback_timeout,
        )
        _logger.info("Output of MTS %s", mts_res.text)
        current_conf.update({"start_datetime": current_conf.end_datetime, "end_datetime": dt_now})
        if current_conf.is_recurring == "onetime":
            current_conf.job_status = "completed"

    def custom_single_action(self, mts_request):
        # to be overloaded by other modules.
        _logger.info("Custom Single Action Called")

    @classmethod
    def datetime_to_iso(cls, dt: datetime):
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + dt.strftime(".%f")[0:4] + "Z"
