from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestResPartner(TransactionCase):
    def setUp(self):
        super().setUp()
        self.odk_config = self.env["odk.config"].create(
            {
                "base_url": "http://test.odk.com",
                "project": "test_project",
                "username": "testuser",
                "password": "testpassword",
                "name": "Test ODK Config",
                "create_date": fields.Datetime.now(),
                "create_uid": 1,
                "write_date": fields.Datetime.now(),
                "write_uid": 1,
            }
        )

        self.partner = self.env["res.partner"].create(
            {"name": "Test Partner", "odk_config_id": self.odk_config.id}
        )

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_fetch_odk_app_users_failure(self, mock_get, mock_login):
        mock_get.return_value.status_code = 500

        mock_login.return_value = "test_session_token"

        with self.assertRaises(UserError):
            self.partner._fetch_odk_app_users()

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("odoo.addons.g2p_odk_user_mapping.models.res_partner.ResPartner._fetch_odk_app_users")
    def test_onchange_odk_config_id(self, mock_fetch, mock_login):
        mock_fetch.return_value = [{"id": 1, "displayName": "User One"}]

        mock_login.return_value = "test_session_token"

        result = self.partner._onchange_odk_config_id()

        self.assertIsNotNone(result, "_onchange_odk_config_id should not return None")
        self.assertIsInstance(result, dict, "_onchange_odk_config_id should return a dictionary")
        self.assertIn("domain", result, "_onchange_odk_config_id result should contain 'domain' key")
        domain = result.get("domain", {})
        self.assertIn("odk_app_user", domain, "'odk_app_user' not found in domain.")
        self.assertIn(("id", "in", [1]), domain.get("odk_app_user", []), "ODK user filter is incorrect.")

    def test_onchange_odk_config_id_no_config(self):
        self.partner.odk_config_id = None

        result = self.partner._onchange_odk_config_id()

        self.assertEqual(result, {"domain": {"odk_app_user": []}})
