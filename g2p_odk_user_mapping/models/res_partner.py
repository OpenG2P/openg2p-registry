import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    odk_config_id = fields.Many2one("odk.config", string="ODK Config")
    odk_app_user = fields.Many2one("odk.app.user", string="ODK App User")

    @api.onchange("odk_config_id")
    def _onchange_odk_config_id(self):
        self.odk_app_user = []
        app_users = []
        if self.odk_config_id:
            app_users = self._fetch_odk_app_users()
            _logger.info(
                "LOG----->ODK APP USER:%s", [f"{user['id']} -{user['displayName']}" for user in app_users]
            )
            return {"domain": {"odk_app_user": [("id", "in", [user["id"] for user in app_users])]}}
        else:
            return {"domain": {"odk_app_user": []}}

    def _fetch_odk_app_users(self):
        self.ensure_one()
        self.odk_config_id.ensure_one()
        url = f"{self.odk_config_id.base_url}/v1/projects/{self.odk_config_id.project}/app-users"
        headers = {
            "Content-Type": "application/json",
            "X-Extended-Metadata": "true",
            "Authorization": f"Bearer {self.odk_config_id.login_get_session_token()}",
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
