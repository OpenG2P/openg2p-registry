from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.g2p_odk_importer.models.odk_client import ODKClient


class TestOdkImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_url = "http://example.com"
        cls.username = "test_user"
        cls.password = "test_password"
        cls.project_id = "5"
        cls.form_id = "test_form_id"
        cls.target_registry = "group"
        cls.json_formatter = "{ name: .name, age: .age }"

        cls.odk_config = cls.env["odk.config"].create(
            {
                "name": "Test ODK Config",
                "base_url": cls.base_url,
                "username": cls.username,
                "password": cls.password,
                "project": cls.project_id,
                "form_id": cls.form_id,
            }
        )

    @patch.object(ODKClient, "login")
    @patch.object(ODKClient, "test_connection")
    def test_test_connection(self, mock_test_connection, mock_login):
        mock_test_connection.return_value = True
        mock_login.return_value = None

        odk_import = self.env["odk.import"].create(
            {
                "odk_config": self.odk_config.id,
                "target_registry": self.target_registry,
                "json_formatter": self.json_formatter,
            }
        )

        result = odk_import.test_connection()

        self.assertTrue(mock_login.called)
        self.assertTrue(mock_test_connection.called)
        self.assertEqual(result["params"]["type"], "success")
        self.assertEqual(result["params"]["message"], "Tested successfully.")

    @patch.object(ODKClient, "login")
    @patch.object(ODKClient, "import_delta_records")
    def test_import_records(self, mock_import_delta_records, mock_login):
        mock_import_delta_records.return_value = {"form_updated": True, "partner_count": 5}
        mock_login.return_value = None

        odk_import = self.env["odk.import"].create(
            {
                "odk_config": self.odk_config.id,
                "target_registry": self.target_registry,
                "json_formatter": self.json_formatter,
            }
        )

        result = odk_import.import_records()

        self.assertTrue(mock_login.called)
        self.assertTrue(mock_import_delta_records.called)

        expected_message = "ODK form 5 records were imported successfully."

        self.assertEqual(result["params"]["type"], "success")
        self.assertEqual(result["params"]["message"], expected_message)

    @patch.object(ODKClient, "login")
    @patch.object(ODKClient, "import_delta_records")
    def test_import_records_no_updates(self, mock_import_delta_records, mock_login):
        mock_import_delta_records.return_value = {}
        mock_login.return_value = None

        odk_import = self.env["odk.import"].create(
            {
                "odk_config": self.odk_config.id,
                "target_registry": self.target_registry,
                "json_formatter": self.json_formatter,
            }
        )

        result = odk_import.import_records()

        self.assertTrue(mock_login.called)
        self.assertTrue(mock_import_delta_records.called)
        self.assertEqual(result["params"]["type"], "warning")
        self.assertEqual(result["params"]["message"], "No new form records were submitted.")
