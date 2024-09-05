import json
import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    odk_config_id = fields.Many2one("odk.config", string="ODK Config")
    odk_app_user = fields.Many2one("odk.app.user", string="ODK App User")
    session = fields.Char(string="Session Token", readonly=True)

    @api.onchange("odk_config_id")
    def _onchange_odk_config_id(self):
        self.odk_app_user = [
            5,
        ]
        if self.odk_config_id:
            base_url = self.odk_config_id.base_url
            project_id = self.odk_config_id.project
            username = self.odk_config_id.username
            password = self.odk_config_id.password
            self._login(base_url, username, password)
            if self.session:
                app_users = self._fetch_app_users(base_url, project_id)
                _logger.info(
                    "LOG----->ODK APP USER:%s"
                    % [f"{user['id']} -{user['displayName']}" for user in app_users]
                )
            return {"domain": {"odk_app_user": [("id", "in", [user["id"] for user in app_users])]}}
        else:
            return {"domain": {"odk_app_user": []}}

    def _login(self, base_url, username, password):
        login_url = f"{base_url}/v1/sessions"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"email": username, "password": password})
        try:
            response = requests.post(login_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            if response.status_code == 200:
                self.session = response.json()["token"]
        except Exception as e:
            _logger.exception("Login failed: %s", e)
            raise ValidationError(f"Login failed: {e}") from e

    def _fetch_app_users(self, base_url, project_id):
        url = f"{base_url}/v1/projects/{project_id}/app-users"
        headers = {
            "Content-Type": "application/json",
            "X-Extended-Metadata": "true",
            "Authorization": f"Bearer {self.session}",
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            app_users_data = response.json()
            query = """
                    DELETE FROM odk_app_user WHERE partner_id = %s
                    """
            self.env.cr.execute(query, (self.id.origin or self.id,))

            for user in app_users_data:
                self.env["odk.app.user"].create(
                    {"name": user["displayName"], "odk_user_id": user["id"], "partner_id": self.id.origin}
                )
            return app_users_data
        else:
            raise UserError(_("Failed to fetch app users"))
