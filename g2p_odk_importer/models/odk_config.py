import base64
import json
import logging
from datetime import datetime, timezone

import jq
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
            and self.session_expires_at > datetime.now(tz=timezone.utc)
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

    def import_records(self, jq_format, target_registry, instance_id=None, last_sync_time=None, skip=0):
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
        partner_count = 0
        for member in data["value"]:
            _logger.debug("ODK RAW DATA:%s" % member)

            mapped_json = jq.first(jq_format, member)
            if target_registry == "individual":
                mapped_json.update({"is_registrant": True, "is_group": False})
            elif target_registry == "group":
                mapped_json.update({"is_registrant": True, "is_group": True})

            self.handle_one2many_fields(mapped_json, target_registry)
            self.handle_media_import(mapped_json, member)

            self.handle_addl_data(mapped_json)

            self.env["res.partner"].sudo().create(mapped_json)
            partner_count += 1
            data.update({"form_updated": True})

        data.update({"partner_count": partner_count})

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

    def handle_one2many_fields(self, mapped_json, target_registry):
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

        if "group_membership_ids" in mapped_json and target_registry == "group":
            individual_ids = []
            relationships_ids = []
            group_membership_data = (
                mapped_json.get("group_membership_ids")
                if mapped_json.get("group_membership_ids") is not None
                else []
            )

            for individual_mem in group_membership_data:
                individual_data = self.get_individual_data(individual_mem)
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
                        },
                    )
                )

    def handle_media_import(self, mapped_json, member):
        self.ensure_one()
        instance_id = member.get("meta", {}).get("instanceID")
        if not instance_id:
            return
        if mapped_json.get("image_1920", None):
            attachm = self.download_attachment(instance_id, mapped_json["image_1920"])
            if attachm:
                mapped_json["image_1920"] = base64.b64encode(attachm)

    def handle_addl_data(self, mapped_json):
        # Override this method to add more data
        return mapped_json

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
