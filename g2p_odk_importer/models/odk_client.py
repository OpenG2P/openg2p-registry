import base64
import json
import logging
import mimetypes
from datetime import datetime

import jq
import pytz
import requests
from dateutil import parser

from odoo import _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ODKClient:
    def __init__(
        self,
        env,
        _id,
        base_url,
        username,
        password,
        project_id,
        form_id,
        target_registry,
        json_formatter=".",
    ):
        self.id = _id
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.project_id = project_id
        self.form_id = form_id
        self.session = None
        self.env = env
        self.json_formatter = json_formatter
        self.target_registry = target_registry

    def login(self):
        login_url = f"{self.base_url}/v1/sessions"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"email": self.username, "password": self.password})
        try:
            response = requests.post(login_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            if response.status_code == 200:
                self.session = response.json()["token"]
        except Exception as e:
            _logger.exception("Login failed: %s", e)
            raise ValidationError(f"Login failed: {e}") from e

    def test_connection(self):
        if not self.session:
            raise ValidationError(_("Session not created"))
        info_url = f"{self.base_url}/v1/users/current"
        headers = {"Authorization": f"Bearer {self.session}"}
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

    # ruff: noqa: C901
    def import_delta_records(self, last_sync_timestamp=None, skip=0):
        url = f"{self.base_url}/v1/projects/{self.project_id}/forms/{self.form_id}.svc/Submissions"
        params = {
            "$skip": skip,
            "$count": "true",
            "$expand": "*",
        }
        if last_sync_timestamp:
            startdate = last_sync_timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            params["$filter"] = f"__system/submissionDate ge {startdate}"

        headers = {"Authorization": f"Bearer {self.session}"}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            _logger.exception("Failed to parse response: %s", e)
            raise ValidationError(f"Failed to parse response: {e}") from e

        # Sort the list of submissions based on the submission_time field if it exists
        data["value"] = sorted(
            data["value"],
            key=lambda x: (
                x.get("submission_time") in (None, ""),  # True for invalid times, sorts to end
                parser.parse(x["submission_time"]) if x.get("submission_time") not in (None, "") else None,
            ),
        )
        partner_count = 0
        for member in data["value"]:
            _logger.info("ODK RAW DATA:%s" % member)
            try:
                mapped_json = jq.first(self.json_formatter, member)
                if self.target_registry == "individual":
                    mapped_json.update({"is_registrant": True, "is_group": False})
                elif self.target_registry == "group":
                    mapped_json.update({"is_registrant": True, "is_group": True})

                self.handle_one2many_fields(mapped_json)
                self.handle_media_import(member, mapped_json)

                updated_mapped_json = self.get_addl_data(mapped_json)

                self.env["res.partner"].sudo().create(updated_mapped_json)
                partner_count += 1
                data.update({"form_updated": True})
            except Exception as e:
                data.update({"form_failed": True})
                _logger.error("An exception occurred%s" % e)
                raise ValidationError(f"The following errors occurred:\n{e}") from e

        data.update({"partner_count": partner_count})

        return data

    def handle_one2many_fields(self, mapped_json):
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
            mapped_json["reg_ids"] = [
                (
                    0,
                    0,
                    {
                        "id_type": self.env["g2p.id.type"]
                        .search([("name", "=", reg_id.get("id_type"))], limit=1)
                        .id,
                        "value": reg_id.get("value"),
                        "expiry_date": reg_id.get("expiry_date"),
                    },
                )
                for reg_id in mapped_json["reg_ids"]
            ]

    def handle_media_import(self, member, mapped_json):
        meta = member.get("meta")
        if not meta:
            return

        instance_id = meta.get("instanceID")
        if not instance_id:
            return

        exit_attachment = self.list_expected_attachments(
            self.base_url, self.project_id, self.form_id, instance_id, self.session
        )
        if not exit_attachment:
            return

        first_image_stored = False
        for attachment in exit_attachment:
            filename = attachment["name"]
            get_attachment = self.download_attachment(
                self.base_url, self.project_id, self.form_id, instance_id, filename, self.session
            )
            attachment_base64 = base64.b64encode(get_attachment).decode("utf-8")
            image_verify = self.is_image(filename)

            if not first_image_stored and image_verify and "image_1920" in mapped_json:
                mapped_json["image_1920"] = attachment_base64
                first_image_stored = True
            else:
                backend_id = (
                    self.env.ref("storage_backend.default_storage_backend").id
                    or self.env["storage.backend"].search([], limit=1).id
                )
                mapped_json["supporting_documents_ids"] = [
                    (
                        0,
                        0,
                        {
                            "backend_id": backend_id,
                            "name": attachment["name"],
                            "data": attachment_base64,
                        },
                    )
                ]

    def get_member_kind(self, record):
        kind_as_str = record.get("kind", None)
        kind = self.env["g2p.group.membership.kind"].search([("name", "=", kind_as_str)], limit=1)
        return kind

    def get_member_relationship(self, source_id, record):
        member_relation = record.get("relationship_with_head", None)
        relation = self.env["g2p.relationship"].search([("name", "=", member_relation)], limit=1)

        if relation:
            return {"source": source_id, "relation": relation.id, "start_date": datetime.now()}

        _logger.warning("No relation defined for member")

        return None

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

    def get_individual_data(self, record):
        name = record.get("name", None)
        given_name = name.split(" ")[0]
        family_name = name.split(" ")[-1]
        dob = self.get_dob(record)
        addl_name = " ".join(name.split(" ")[1:-1])
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

    def get_addl_data(self, mapped_json):
        # Override this method to add more data
        return mapped_json

    def is_image(self, filename):
        mimetype, _ = mimetypes.guess_type(filename)
        return mimetype and mimetype.startswith("image")

    def list_expected_attachments(self, base_url, project_id, form_id, instance_id, session_token):
        url = f"{base_url}/v1/projects/{project_id}/forms/{form_id}/submissions/{instance_id}/attachments"
        headers = {"Authorization": f"Bearer {session_token}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def download_attachment(self, base_url, project_id, form_id, instance_id, filename, session_token):
        url = (
            f"{base_url}/v1/projects/{project_id}/forms/{form_id}/"
            f"submissions/{instance_id}/attachments/{filename}"
        )
        headers = {"Authorization": f"Bearer {session_token}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.content

    #  Fetch Record using Instance ID
    def import_record_by_instance_id(self, instance_id, last_sync_timestamp=None):
        url = (
            f"{self.base_url}/v1/projects/{self.project_id}/forms/{self.form_id}.svc/"
            f"Submissions('{instance_id}')"
        )
        headers = {"Authorization": f"Bearer {self.session}"}
        params = {
            "$skip": 0,
            "$count": "true",
            "$expand": "*",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            _logger.exception("Failed to parse response by using instance ID: %s", e)
            raise ValidationError(f"Failed to parse response by using instance ID: {e}") from e

        _logger.info(f"ODK RAW DATA by instance ID %s {instance_id} {data}")

        if last_sync_timestamp:
            last_sync_time = pytz.UTC.localize(last_sync_timestamp)
        else:
            last_sync_time = None

        try:
            for member in data["value"]:
                submission_date_str = member.get("__system", {}).get("submissionDate")
                if submission_date_str:
                    # Parse submissionDate to a timezone-aware datetime object
                    submission_date = parser.isoparse(submission_date_str)
                    if last_sync_time and last_sync_time < submission_date:
                        raise UserError(
                            _("Future records cannot be fetched before the regular import occurs.")
                        )

                mapped_json = jq.first(self.json_formatter, member)
                if self.target_registry == "individual":
                    mapped_json.update({"is_registrant": True, "is_group": False})
                elif self.target_registry == "group":
                    mapped_json.update({"is_registrant": True, "is_group": True})

                self.handle_one2many_fields(mapped_json)
                self.handle_media_import(member, mapped_json)

                updated_mapped_json = self.get_addl_data(mapped_json)
                self.env["res.partner"].sudo().create(updated_mapped_json)

            data.update({"form_updated": True})

        except Exception as e:
            data.update({"form_failed": True})
            _logger.error("An exception occurred by instanceID%s" % e)
            raise ValidationError(f"The following errors occurred by instanceID:\n{e}") from e

        return data
