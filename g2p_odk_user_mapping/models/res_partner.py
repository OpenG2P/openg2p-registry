import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    odk_config_id = fields.Many2one("odk.config", string="ODK Config")
    odk_app_user = fields.Many2one(
        "odk.app.user",
        string="ODK App User",
        domain="[('odk_config_id', '=', odk_config_id)]",
    )

    def fetch_odk_app_users(self):
        """Fetch ODK App Users via API call and create only new users."""
        self.ensure_one()

        url = f"{self.odk_config_id.base_url}/v1/projects/{self.odk_config_id.project}/app-users"
        headers = {
            "Content-Type": "application/json",
            "X-Extended-Metadata": "true",
            "Authorization": f"Bearer {self.odk_config_id.login_get_session_token()}",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            app_users_data = response.json()

            existing_odk_users = set(
                self.env["odk.app.user"]
                .search([("odk_config_id", "=", self.odk_config_id.id)])
                .mapped("odk_user_id")
            )

            new_users = []
            for user in app_users_data:
                odk_user_id = user.get("id")
                display_name = user.get("displayName")

                if odk_user_id not in existing_odk_users:
                    new_users.append(
                        {
                            "name": display_name,
                            "odk_user_id": odk_user_id,
                            "odk_config_id": self.odk_config_id.id,
                        }
                    )

            if new_users:
                self.env["odk.app.user"].create(new_users)
                message = _("ODK App Users fetched successfully.")
                message_type = "success"
            else:
                message = _("No new users found.")
                message_type = "warning"

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": message_type,
                    "message": message,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }

        except requests.exceptions.RequestException as e:
            raise UserError(_("Failed to fetch ODK App Users: %s") % str(e)) from e
