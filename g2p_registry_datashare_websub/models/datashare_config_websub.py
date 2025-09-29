import logging
import os
from datetime import datetime, timedelta
from urllib.parse import parse_qs

import jq
import requests

from odoo import _, api, fields, models, tools

from ..json_encoder import WebSubJSONEncoder

_logger = logging.getLogger(__name__)

WEBSUB_BASE_URL = os.getenv("WEBSUB_BASE_URL", "http://websub/hub")
WEBSUB_AUTH_URL = os.getenv(
    "WEBSUB_AUTH_URL",
    "http://keycloak.keycloak/realms/master/protocol/openid-connect/token",
)
WEBSUB_AUTH_CLIENT_ID = os.getenv("WEBSUB_AUTH_CLIENT_ID", "openg2p-admin-client")
WEBSUB_AUTH_CLIENT_SECRET = os.getenv("WEBSUB_AUTH_CLIENT_SECRET", "")
WEBSUB_AUTH_GRANT_TYPE = os.getenv("WEBSUB_AUTH_GRANT_TYPE", "client_credentials")


class G2PDatashareConfigWebsubExtraField(models.Model):
    _name = "g2p.datashare.config.websub.extra.field"
    _description = "G2P Datashare Config WebSub Extra Field"

    name = fields.Char()
    config_id = fields.Many2one("g2p.datashare.config.websub", ondelete="cascade")
    data_type = fields.Selection(
        [
            ("string", "String"),
            ("json", "JSON"),
            ("jwt", "JWT"),
            # Not implemented
            # ("cwt", "CWT"),
        ]
    )
    body_string = fields.Char(string="Body")


class G2PDatashareConfigWebsub(models.Model):
    _name = "g2p.datashare.config.websub"
    _description = "G2P Datashare Config WebSub"

    name = fields.Char(required=True)

    partner_id = fields.Char(string="Partner ID")

    event_type = fields.Selection(
        [
            ("WEBSUB_GROUP_CREATED", "Group Created"),
            ("WEBSUB_GROUP_UPDATED", "Group Updated"),
            ("WEBSUB_GROUP_DELETED", "Group Deleted"),
            ("WEBSUB_INDIVIDUAL_CREATED", "Individual Created"),
            ("WEBSUB_INDIVIDUAL_UPDATED", "Individual Updated"),
            ("WEBSUB_INDIVIDUAL_DELETED", "Individual Deleted"),
        ],
        required=True,
    )
    topic_joiner = fields.Char(default="/")

    transform_data_jq = fields.Text(
        string="Data Transform JQ Expression",
        default="""{
    ts_ms: .curr_datetime,
    event: .publisher.event_type,
    groupData: .record_data
}""",
    )
    condition_jq = fields.Text(string="Condition JQ Expression", default="true")

    extra_fields = fields.One2many("g2p.datashare.config.websub.extra.field", "config_id")

    encryption_provider_id = fields.Many2one("g2p.encryption.provider")

    websub_base_url = fields.Char("WebSub Base URL", default=WEBSUB_BASE_URL)
    websub_auth_url = fields.Char("WebSub Auth URL (Token Endpoint)", default=WEBSUB_AUTH_URL)
    websub_auth_client_id = fields.Char("WebSub Auth Client ID", default=WEBSUB_AUTH_CLIENT_ID)
    websub_auth_client_secret = fields.Char(default=WEBSUB_AUTH_CLIENT_SECRET)
    websub_auth_grant_type = fields.Char(default=WEBSUB_AUTH_GRANT_TYPE)
    websub_api_timeout = fields.Integer("WebSub API Timeout", default=10)

    websub_access_token = fields.Char()
    websub_access_token_expiry = fields.Datetime()

    active = fields.Boolean(required=True, default=True)

    @api.model_create_multi
    def create(self, vals):
        _logger.debug("WebSub Config Create - Creating new websub config(s): %s", vals)
        res = super().create(vals)
        for rec in res:
            _logger.debug(
                "WebSub Config Create - Auto-registering topic for new config '%s' (ID: %s)", rec.name, rec.id
            )
            rec.register_websub_event()
        return res

    def write(self, vals):
        _logger.debug("WebSub Config Write - Updating config(s) with values: %s", vals)

        try:
            if isinstance(vals, dict) and ("event_type" in vals or "partner_id" in vals):
                _logger.debug("WebSub Config Write - Topic-related fields changed, deregistering old topics")
                for rec in self:
                    _logger.debug(
                        "WebSub Config Write - Deregistering old topic for config '%s' (ID: %s)",
                        rec.name,
                        rec.id,
                    )
                    rec.deregister_websub_event()
        except Exception:
            _logger.exception("WebSub - Changed event: couldnt deregister")

        res = super().write(vals)

        if isinstance(vals, dict) and ("event_type" in vals or "partner_id" in vals):
            _logger.debug("WebSub Config Write - Re-registering topics with new values")
            for rec in self:
                _logger.debug(
                    "WebSub Config Write - Re-registering topic for config '%s' (ID: %s)", rec.name, rec.id
                )
                rec.register_websub_event()
        return res

    def unlink(self):
        force = self._context.get("force_delete", False)
        _logger.debug("WebSub Config Unlink - Deleting config(s), force_delete: %s", force)

        for rec in self:
            _logger.debug(
                "WebSub Config Unlink - Deregistering topic before deletion for config '%s' (ID: %s)",
                rec.name,
                rec.id,
            )
            try:
                rec.deregister_websub_event()
            except Exception as e:
                _logger.exception("Failed to deregister websub publisher")
                if not force:
                    raise e
        return super().unlink()

    @api.model
    def publish_event(self, event_type, data: dict, condition_override=None):
        _logger.debug(
            "WebSub Publish Event - Looking for publishers for event_type: %s, data: %s", event_type, data
        )

        publishers = self.get_publishers(event_type)
        if not publishers:
            _logger.debug("WebSub Publish Event - No publishers found for event_type: %s", event_type)
            return

        _logger.debug(
            "WebSub Publish Event - Found %d publisher(s) for event_type: %s. Publishers: %s",
            len(publishers),
            event_type,
            [f"{p.name} (ID: {p.id})" for p in publishers],
        )

        for publisher in publishers:
            _logger.debug(
                "WebSub Publish Event - Processing publisher '%s' (ID: %s)", publisher.name, publisher.id
            )
            publisher.publish_by_publisher(data, condition_override=condition_override)

    def publish_by_publisher(self, data: dict, condition_override=None):
        self.ensure_one()

        # Determine if this is a manual or automatic publish
        import inspect

        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_method = caller_frame.f_code.co_name if caller_frame else "unknown"
        caller_filename = caller_frame.f_code.co_filename if caller_frame else "unknown"

        # Check if this is called from manual trigger
        is_manual = "manual_trigger" in caller_filename or "publish_records_by_ids" in caller_method

        publish_type = "MANUAL" if is_manual else "AUTOMATIC"

        _logger.info(
            "WEBSUB PUBLISH BY PUBLISHER - %s - Config: '%s' (ID: %s), Record ID: %s, Caller: %s",
            publish_type,
            self.name,
            self.id,
            data.get("id"),
            caller_method,
        )

        _logger.debug(
            "WebSub Publish By Publisher - Starting for config '%s' (ID: %s), record ID: %s",
            self.name,
            self.id,
            data.get("id"),
        )

        try:
            web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
            curr_datetime = f'{datetime.now().isoformat(timespec = "milliseconds")}Z'

            _logger.debug(
                "WebSub Publish By Publisher - Base URL: %s, Current datetime: %s",
                web_base_url,
                curr_datetime,
            )

            record_id = data["id"]
            record = self.env["res.partner"].browse(record_id)

            _logger.debug(
                "WebSub Publish By Publisher - Partner record exists: %s, Partner name: %s",
                record.exists(),
                record.name if record.exists() else "N/A",
            )

            if not record.exists():
                _logger.error(
                    "WebSub- Partner record with ID %s does not exist, aborting publish",
                    record_id,
                )
                return

            _logger.debug(
                "WebSub Publish By Publisher - Fetching full record data for partner ID: %s", record_id
            )

            try:
                record_data = self.get_full_record_data(record)
                _logger.debug(
                    "WebSub Publish By Publisher - Raw record data retrieved, length: %s",
                    len(record_data) if record_data else 0,
                )

                if record_data:
                    record_data = record_data[0]
                    _logger.debug(
                        "WebSub Publish By Publisher - Record data keys: %s",
                        list(record_data.keys()) if isinstance(record_data, dict) else "Not a dict",
                    )
                else:
                    _logger.warning(
                        "WebSub Publish By Publisher - No record data retrieved for partner ID: %s", record_id
                    )

            except Exception as e:
                _logger.error(
                    "WebSub Publish By Publisher - Error fetching record data for partner ID %s: %s",
                    record_id,
                    str(e),
                )
                raise

            _logger.debug("WebSub Publish By Publisher - Building context data structure")

            try:
                publisher_data = self.read()[0]
                _logger.debug(
                    "WebSub Publish By Publisher - Publisher data keys: %s",
                    list(publisher_data.keys()) if isinstance(publisher_data, dict) else "Not a dict",
                )

                context_data = {
                    "web_base_url": web_base_url,
                    "publisher": publisher_data,
                    "curr_datetime": curr_datetime,
                    "data": data,
                    "record_data": record_data,
                }

                _logger.debug(
                    "WebSub Publish By Publisher - Context data structure built, converting to JSON dict"
                )

                record_data = WebSubJSONEncoder.python_dict_to_json_dict(context_data)

                _logger.debug("WebSub Publish By Publisher - JSON conversion complete")

            except Exception as e:
                _logger.error("WebSub Publish By Publisher - Error building context data: %s", str(e))
                raise

            _logger.debug(
                "WebSub Publish By Publisher - Handling extra fields, count: %s", len(self.extra_fields)
            )

            try:
                self.handle_extra_fields(record_data)
                _logger.debug("WebSub Publish By Publisher - Extra fields handled successfully")
            except Exception as e:
                _logger.error("WebSub Publish By Publisher - Error handling extra fields: %s", str(e))
                raise

            # Check condition
            condition_expr = condition_override or self.condition_jq
            _logger.debug("WebSub Publish By Publisher - Evaluating condition: %s", condition_expr)

            try:
                condition_result = jq.first(condition_expr, record_data)
                _logger.debug(
                    "WebSub Publish By Publisher - Condition result: %s (type: %s)",
                    condition_result,
                    type(condition_result).__name__,
                )
            except Exception as e:
                _logger.error(
                    "WebSub Publish By Publisher - Error evaluating condition '%s': %s",
                    condition_expr,
                    str(e),
                )
                raise

            if not condition_result:
                _logger.debug(
                    "WebSub Publish By Publisher - Condition failed, skipping publish for config '%s'",
                    self.name,
                )
                return

            _logger.debug(
                "WebSub Publish By Publisher - Condition passed, transforming data using JQ: %s",
                self.transform_data_jq,
            )

            try:
                data_transformed = jq.first(
                    self.transform_data_jq,
                    record_data,
                )

                _logger.debug(
                    "WebSub Publish By Publisher - Data transformation complete, result type: %s",
                    type(data_transformed).__name__,
                )

                # Log a preview of transformed data
                if isinstance(data_transformed, dict):
                    _logger.debug(
                        "WebSub Publish By Publisher - Transformed data keys: %s",
                        list(data_transformed.keys()),
                    )
                else:
                    data_str = str(data_transformed)
                    preview = data_str[:200] + "..." if len(data_str) > 200 else data_str
                    _logger.debug("WebSub Publish By Publisher - Transformed data preview: %s", preview)

            except Exception as e:
                _logger.error(
                    "WebSub Publish By Publisher - Error transforming data with JQ '%s': %s",
                    self.transform_data_jq,
                    str(e),
                )
                raise

            _logger.debug("WebSub Publish By Publisher - Proceeding to WebSub publish")

            self.publish_event_websub(data_transformed)

            _logger.debug(
                "WebSub Publish By Publisher - Publish completed successfully for config '%s'", self.name
            )

        except Exception as e:
            _logger.error(
                "WebSub Publish By Publisher - Fatal error in publish process for config '%s' (ID: %s): %s",
                self.name,
                self.id,
                str(e),
            )
            raise

    def publish_event_websub(self, data):
        self.ensure_one()

        try:
            # Build topic name for logging
            topic_name = (
                f"{self.partner_id}" f"{self.topic_joiner if self.partner_id else ''}" f"{self.event_type}"
            )

            _logger.debug(
                "WebSub Publish - Starting for config '%s' (ID: %s). Topic: %s, URL: %s",
                self.name,
                self.id,
                topic_name,
                self.websub_base_url,
            )

            _logger.debug(
                "WebSub Publish - Topic components: partner_id='%s', topic_joiner='%s', event_type='%s'",
                self.partner_id,
                self.topic_joiner,
                self.event_type,
            )

            # Validate data
            if data is None:
                _logger.error("WebSub Publish - Data is None, cannot publish")
                raise ValueError("WebSub Publish: Data cannot be None")

            # Log the data being published (truncated if too large)
            data_str = str(data)
            if len(data_str) > 1000:
                data_preview = data_str[:500] + "..." + data_str[-500:]
            else:
                data_preview = data_str

            _logger.debug("WebSub Publish - Data payload (preview): %s", data_preview)

            _logger.debug(
                "WebSub Publish - Data type: %s, Data size: %s bytes", type(data).__name__, len(data_str)
            )

            # Get access token
            _logger.debug("WebSub Publish - Getting access token")
            try:
                token = self.get_access_token()
                _logger.debug(
                    "WebSub Publish - Access token obtained, length: %s", len(token) if token else 0
                )
                if not token:
                    _logger.error("WebSub Publish - No access token obtained")
                    raise ValueError("WebSub Publish: No access token available")
            except Exception as e:
                _logger.error("WebSub Publish - Error getting access token: %s", str(e))
                raise

            # Prepare request
            request_params = {
                "hub.mode": "publish",
                "hub.topic": topic_name,
            }

            _logger.debug("WebSub Publish - Request params: %s", request_params)

            headers = {"Authorization": f"Bearer {token}"}
            _logger.debug(
                "WebSub Publish - Request headers: %s",
                {
                    k: v[:20] + "..." if k == "Authorization" and len(v) > 20 else v
                    for k, v in headers.items()
                },
            )

            _logger.debug("WebSub Publish - Making HTTP POST request to: %s", self.websub_base_url)

            _logger.debug("WebSub Publish - Request timeout: %s seconds", self.websub_api_timeout)

            # Make the request
            try:
                res = requests.post(
                    self.websub_base_url,
                    params=request_params,
                    headers=headers,
                    json=data,
                    timeout=self.websub_api_timeout,
                )

                _logger.debug("WebSub Publish - HTTP request completed, status code: %s", res.status_code)

            except requests.exceptions.Timeout as e:
                _logger.error(
                    "WebSub Publish - Request timeout after %s seconds: %s", self.websub_api_timeout, str(e)
                )
                raise
            except requests.exceptions.ConnectionError as e:
                _logger.error("WebSub Publish - Connection error to %s: %s", self.websub_base_url, str(e))
                raise
            except requests.exceptions.RequestException as e:
                _logger.error("WebSub Publish - Request error: %s", str(e))
                raise

            # Log response details
            _logger.debug(
                "WebSub Publish - Raw response: Status: %s, Text: %s, Headers: %s",
                res.status_code,
                res.text,
                dict(res.headers),
            )

            # Check for HTTP errors
            try:
                res.raise_for_status()
                _logger.debug("WebSub Publish - HTTP status check passed")
            except requests.exceptions.HTTPError as e:
                _logger.error(
                    "WEBSUB ERROR - Config: '%s' (ID: %s), Topic: %s, Status: %s, Error: %s, Response: %s",
                    self.name,
                    self.id,
                    topic_name,
                    res.status_code,
                    str(e),
                    res.text,
                )
                _logger.error(
                    "WebSub Publish - HTTP error %s: %s. Response text: %s", res.status_code, str(e), res.text
                )
                raise

            _logger.info(
                "WEBSUB HTTP PUBLISH SUCCESS - Config: '%s' (ID: %s), Topic: %s, Status: %s, Response: %s",
                self.name,
                self.id,
                topic_name,
                res.status_code,
                res.text,
            )

            _logger.debug("WebSub Publish Success. Response: %s. Headers: %s", res.text, res.headers)

            # Parse and validate response
            _logger.debug("WebSub Publish - Parsing response text")
            try:
                parsed_res = parse_qs(res.text)
                _logger.debug("WebSub Publish - Parsed response: %s", parsed_res)
            except Exception as e:
                _logger.error("WebSub Publish - Error parsing response text '%s': %s", res.text, str(e))
                raise

            # Validate hub response
            hub_mode = parsed_res.get("hub.mode", [])
            _logger.debug("WebSub Publish - Hub mode from response: %s", hub_mode)

            if not len(hub_mode) or hub_mode[0].lower() != "accepted":
                _logger.error(
                    "WebSub Publish - Invalid hub response. Expected 'accepted', got: %s. Full response: %s",
                    hub_mode[0] if hub_mode else "None",
                    parsed_res,
                )
                raise ValueError("WebSub Publish: Invalid hub response")

            _logger.debug(
                "WebSub Publish - Successfully completed for config '%s', topic: %s", self.name, topic_name
            )

        except Exception as e:
            _logger.error(
                "WebSub Publish - Fatal error for config '%s' (ID: %s), topic: %s. Error: %s",
                self.name,
                self.id,
                topic_name if "topic_name" in locals() else "Unknown",
                str(e),
            )
            raise

    def register_websub_event(self, mode="register"):
        self.ensure_one()

        # Build topic name for logging
        topic_name = (
            f"{self.partner_id}" f"{self.topic_joiner if self.partner_id else ''}" f"{self.event_type}"
        )

        _logger.debug(
            "WebSub Topic %s - Starting request for config '%s' (ID: %s). Topic: %s, URL: %s",
            mode.title(),
            self.name,
            self.id,
            topic_name,
            self.websub_base_url,
        )

        token = self.get_access_token()

        request_data = {
            "hub.mode": mode,
            "hub.topic": topic_name,
        }

        _logger.debug("WebSub Topic %s - Request data: %s", mode.title(), request_data)

        res = requests.post(
            self.websub_base_url,
            headers={"Authorization": f"Bearer {token}"},
            data=request_data,
            timeout=self.websub_api_timeout,
        )
        res.raise_for_status()

        _logger.debug(
            "WebSub Topic %s - Raw response: Status: %s, Text: %s, Headers: %s",
            mode.title(),
            res.status_code,
            res.text,
            dict(res.headers),
        )

        _logger.info(
            "WebSub Topic Registration/Deregistration Successful. Response: %s. Headers: %s",
            res.text,
            res.headers,
        )
        res = parse_qs(res.text)
        res = {k: v[0] if len(v) else None for k, v in res.items()}
        if not (
            (res.get("hub.mode") and res["hub.mode"].lower() == "accepted")
            or (res.get("hub.reason") and "already register" in res["hub.reason"].lower())
        ):
            raise ValueError("WebSub Topic Register: Invalid hub response")

    def deregister_websub_event(self):
        _logger.debug(
            "WebSub Deregister - Starting deregistration for config '%s' (ID: %s)", self.name, self.id
        )
        return self.register_websub_event(mode="deregister")

    def handle_extra_fields(self, record_data):
        extra_field_data = {}
        for extra_field in self.extra_fields:
            f_data = None
            if extra_field.data_type == "json":
                f_data = jq.first(extra_field.body_string, record_data)
            elif extra_field.data_type == "jwt":
                encryption_provider = self.get_encryption_provider()
                f_data = jq.first(extra_field.body_string, record_data)
                f_data = encryption_provider.jwt_sign(f_data)
            else:  # elif extra_field.data_type == "string"
                f_data = str(jq.first(extra_field.body_string, record_data))
            extra_field_data[extra_field.name] = f_data
        record_data["extra_fields"] = extra_field_data

    def get_access_token(self):
        self.ensure_one()

        _logger.debug("WebSub Token - Checking access token for config '%s' (ID: %s)", self.name, self.id)

        # Check if we have a valid existing token
        current_time = datetime.now()
        if (
            self.websub_access_token
            and self.websub_access_token_expiry
            and self.websub_access_token_expiry > current_time
        ):
            time_remaining = self.websub_access_token_expiry - current_time
            _logger.debug(
                "WebSub Token - Using existing valid token (expires: %s, time remaining: %s)",
                self.websub_access_token_expiry,
                time_remaining,
            )
            return self.websub_access_token

        _logger.debug(
            "WebSub Token - Need new token. Current token: %s, Expiry: %s, Current time: %s",
            "Present" if self.websub_access_token else "None",
            self.websub_access_token_expiry,
            current_time,
        )

        _logger.debug("WebSub Token - Requesting new token from: %s", self.websub_auth_url)

        # Validate auth configuration
        if not self.websub_auth_url:
            _logger.error("WebSub Token - No auth URL configured")
            raise ValueError("WebSub Token: No auth URL configured")

        if not self.websub_auth_client_id:
            _logger.error("WebSub Token - No client ID configured")
            raise ValueError("WebSub Token: No client ID configured")

        data = {
            "client_id": self.websub_auth_client_id,
            "client_secret": self.websub_auth_client_secret,
            "grant_type": self.websub_auth_grant_type,
        }

        _logger.debug(
            "WebSub Token - Request data: client_id=%s, grant_type=%s, client_secret=%s",
            self.websub_auth_client_id,
            self.websub_auth_grant_type,
            "Present" if self.websub_auth_client_secret else "None",
        )

        try:
            _logger.debug(
                "WebSub Token - Making POST request with timeout: %s seconds", self.websub_api_timeout
            )

            response = requests.post(self.websub_auth_url, data=data, timeout=self.websub_api_timeout)

            _logger.debug(
                "WebSub Token - Response status: %s, Response text: %s", response.status_code, response.text
            )

            response.raise_for_status()

        except requests.exceptions.Timeout as e:
            _logger.error(
                "WebSub Token - Request timeout after %s seconds: %s", self.websub_api_timeout, str(e)
            )
            raise
        except requests.exceptions.ConnectionError as e:
            _logger.error("WebSub Token - Connection error to %s: %s", self.websub_auth_url, str(e))
            raise
        except requests.exceptions.HTTPError as e:
            _logger.error(
                "WebSub Token - HTTP error %s: %s. Response: %s", response.status_code, str(e), response.text
            )
            raise
        except requests.exceptions.RequestException as e:
            _logger.error("WebSub Token - Request error: %s", str(e))
            raise

        try:
            response_json = response.json()
            _logger.debug(
                "WebSub Token - Parsed JSON response keys: %s",
                list(response_json.keys()) if isinstance(response_json, dict) else "Not a dict",
            )
        except Exception as e:
            _logger.error("WebSub Token - Error parsing JSON response '%s': %s", response.text, str(e))
            raise

        access_token = response_json.get("access_token", None)
        token_exp = response_json.get("expires_in", None)

        _logger.debug(
            "WebSub Token - Token extracted: %s, Expires in: %s",
            "Present" if access_token else "None",
            token_exp,
        )

        if not access_token:
            _logger.error("WebSub Token - No access_token in response: %s", response_json)
            raise ValueError("WebSub Token: No access_token in response")

        # Calculate expiry time
        try:
            if isinstance(token_exp, int):
                expiry_time = datetime.now() + timedelta(seconds=token_exp)
            elif isinstance(token_exp, str):
                expiry_time = datetime.fromisoformat(token_exp)
            else:
                expiry_time = token_exp

            _logger.debug("WebSub Token - Calculated expiry time: %s", expiry_time)

        except Exception as e:
            _logger.error("WebSub Token - Error calculating expiry time from '%s': %s", token_exp, str(e))
            # Default to 1 hour if we can't parse expiry
            expiry_time = datetime.now() + timedelta(hours=1)
            _logger.debug("WebSub Token - Using default expiry time: %s", expiry_time)

        # Save the token
        try:
            self.sudo().write(
                {
                    "websub_access_token": access_token,
                    "websub_access_token_expiry": expiry_time,
                }
            )
            _logger.debug("WebSub Token - Token saved successfully, expires: %s", expiry_time)
        except Exception as e:
            _logger.error("WebSub Token - Error saving token: %s", str(e))
            raise

        return access_token

    @tools.ormcache("event_type")
    def get_publishers(self, event_type):
        return self.search([("event_type", "=", event_type), ("active", "=", True)])

    def get_full_record_data(self, records):
        res_partner_fields = [
            fname
            for fname in self.env["res.partner"]._fields
            if not (fname.startswith("image_") or fname.startswith("avatar_"))
        ]
        g2p_group_membership_fields = [
            fname
            for fname in self.env["g2p.group.membership"]._fields
            if not (fname.startswith("image_") or fname.startswith("avatar_"))
        ]
        response = records.read(fields=res_partner_fields)
        for i, rec in enumerate(records):
            response[i]["image"] = self.get_image_base64_data_in_url((rec.image_1920 or b"").decode())
            response[i]["reg_ids"] = {reg_id.id_type.name: reg_id.value for reg_id in rec.reg_ids}
            if rec.is_group:
                members = rec.group_membership_ids
                members_data = members.read(fields=g2p_group_membership_fields)
                member_individual_data = self.get_full_record_data(members.individual)
                for j in range(len(members)):
                    members_data[j]["individual"] = member_individual_data[j]
                response[i]["group_membership_ids"] = members_data
        return response

    @api.model
    def get_image_base64_data_in_url(self, image_base64: str) -> str:
        if not image_base64:
            return None
        image = tools.base64_to_image(image_base64)
        return f"data:image/{image.format.lower()};base64,{image_base64}"

    def get_encryption_provider(self):
        self.ensure_one()
        prov = self.encryption_provider_id
        if not prov:
            prov = self.env.ref("g2p_encryption.encryption_provider_default")
        return prov

    def open_manual_trigger_wizard(self):
        self.ensure_one()
        is_group = "GROUP" in self.event_type
        return {
            "name": _("Publish Records Manually"),
            "view_mode": "form",
            "res_model": "g2p.datashare.config.websub.manual.trigger",
            "view_id": self.env.ref(
                "g2p_registry_datashare_websub.view_datashare_websub_manual_trigger_form"
            ).id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {
                "default_config_id": self.id,
                "default_domain": f'[("is_registrant","=",True),("is_group","=",{is_group})]',
            },
        }

    def manual_register_websub_action(self):
        for rec in self:
            rec.register_websub_event()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Synced with Websub"),
                "message": _("Publisher(s) synced with Websub."),
                "sticky": True,
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_publish_existing_records(self):
        """Open wizard to publish existing records in batches"""
        self.ensure_one()
        return {
            "name": _("Publish Existing Records"),
            "view_mode": "form",
            "res_model": "g2p.websub.batch.publish",
            "view_id": self.env.ref("g2p_registry_datashare_websub.view_websub_batch_publish_form").id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {
                "default_config_id": self.id,
                "default_name": f"Batch Publish - {self.name}",
                "default_batch_size": 100,
            },
        }
