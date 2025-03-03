import json
import logging
from datetime import datetime, timezone

import requests
from dateutil import parser as dateutil_parser

from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class OdkConfig(models.Model):
    _name = "odk.config"
    _description = "ODK Configuration"

    name = fields.Char(required=True)
    base_url = fields.Char(string="Base URL", required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    project = fields.Char(required=False)
    form_id = fields.Char(string="Form ID", required=False)

    session_token = fields.Char()
    session_expires_at = fields.Datetime()

    def login_get_session_token(self):
        self.ensure_one()
        if (
            self.session_token
            and self.session_expires_at
            and self.session_expires_at > datetime.now().astimezone(timezone.utc).replace(tzinfo=None)
        ):
            return self.session_token
        login_url = f"{self.base_url}/v1/sessions"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"email": self.username, "password": self.password})
        try:
            response = requests.post(login_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            if response.status_code == 200:
                response_json = response.json()
                self.session_token = response_json["token"]
                self.session_expires_at = (
                    dateutil_parser.parse(response_json["expiresAt"])
                    .astimezone(timezone.utc)
                    .replace(tzinfo=None)
                )
                return response_json["token"]
        except Exception as e:
            _logger.exception("Login failed: %s", e)
            raise ValidationError(f"Login failed: {e}") from e

    def test_connection(self):
        self.ensure_one()
        info_url = f"{self.base_url}/v1/users/current"
        headers = {"Authorization": f"Bearer {self.login_get_session_token()}"}
        try:
            response = requests.get(info_url, headers=headers, timeout=10)
            response.raise_for_status()
            if response.status_code == 200:
                user = response.json()
                _logger.info(f'Connected to ODK Central as {user["displayName"]}')
                return True
        except Exception as e:
            _logger.exception("Connection test failed: %s", e)
            raise ValidationError(f"Connection test failed: {e}") from e

    def download_records(self, instance_id=None, last_sync_time=None, skip=0):
        self.ensure_one()
        url = f"{self.base_url}/v1/projects/{self.project}/forms/{self.form_id}.svc/Submissions"
        params = {
            "$skip": skip,
            "$count": "true",
            "$expand": "*",
        }
        if instance_id:
            url += f"('{instance_id}')"
        if last_sync_time:
            startdate = last_sync_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            params["$filter"] = f"__system/submissionDate ge {startdate}"

        headers = {"Authorization": f"Bearer {self.login_get_session_token()}"}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            _logger.exception("Failed to parse response: %s", e)
            raise ValidationError(f"Failed to parse response: {e}") from e

        # Sort the list of submissions based on the submission_time field if it exists
        data["value"] = sorted(
            data["value"],
            key=lambda x: (
                # True for invalid times, sorts to end
                x.get("submission_time") in (None, ""),
                dateutil_parser.parse(x["submission_time"])
                if x.get("submission_time") not in (None, "")
                else None,
            ),
        )
        return data

    def get_submissions(self, fields=None, last_sync_time=None):
        self.ensure_one()
        # Construct the API endpoint
        endpoint = f"{self.base_url}/v1/projects/{self.project}/forms/{self.form_id}.svc/Submissions"

        # Add query parameters to fetch only specific fields and filter by last sync time
        params = {}
        if fields:
            params["$select"] = fields
        if last_sync_time:
            startdate = last_sync_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            params["$filter"] = f"__system/submissionDate ge {startdate}"
        submissions = []
        headers = {"Authorization": f"Bearer {self.login_get_session_token()}"}

        while endpoint:
            # Make the API request
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            # Append the submissions
            data = response.json()
            if isinstance(data, dict):
                submissions.extend(data["value"])
            else:
                _logger.error("Unexpected response format: expected a dict of submissions")
                break

            # Handle pagination
            endpoint = None

        return submissions

    def list_expected_attachments(self, instance_id):
        url = (
            f"{self.base_url}/v1/projects/{self.project}"
            f"/forms/{self.form_id}/submissions/{instance_id}/attachments"
        )
        headers = {"Authorization": f"Bearer {self.login_get_session_token()}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def download_attachment(self, instance_id, filename):
        url = (
            f"{self.base_url}/v1/projects/{self.project}/forms/{self.form_id}/"
            f"submissions/{instance_id}/attachments/{filename}"
        )
        headers = {"Authorization": f"Bearer {self.login_get_session_token()}"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.content
