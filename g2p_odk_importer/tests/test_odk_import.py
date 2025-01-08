from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestOdkImport(TransactionCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.odk_config = self.env["odk.config"].create(
            {
                "name": "Test ODK Config",
                "base_url": "http://example.com",
                "username": "test_user",
                "password": "test_password",
                "project": 1,
                "form_id": "test_form_id",
            }
        )

        self.odk_import = self.env["odk.import"].create(
            {
                "odk_config": self.odk_config.id,
                "json_formatter": "{ name: .name, age: .age }",
                "target_registry": "individual",
                "last_sync_time": datetime.now() - timedelta(days=1),
                "job_status": "draft",
                "interval_hours": 1,
                "enable_import_by_instance_id": True,
            }
        )

    def test_fetch_record_by_instance_id(self):
        # Test fetch record by instance ID method
        with (
            patch.object(self.odk_config, "login_get_session_token") as mock_login,
            patch.object(self.odk_config, "import_record_by_instance_id") as mock_import_record,
        ):
            mock_login.return_value = "test_token"
            mock_import_record.return_value = {"form_updated": True}

            self.odk_import.instance_id = "test_instance_id"
            result = self.odk_import.fetch_record_by_instance_id()

            self.assertEqual(result["params"]["type"], "success")

            self.odk_import.instance_id = False
            with self.assertRaises(UserError):
                self.odk_import.fetch_record_by_instance_id()

    def test_test_connection(self):
        # Test connection method
        with patch.object(self.odk_config, "test_connection") as mock_test_connection:
            mock_test_connection.return_value = True
            result = self.odk_import.test_connection()
        self.assertEqual(result["params"]["message"], "Tested successfully.")

    def test_process_instance_id(self):
        # Test processing instance ID method
        instance_id = self.env["odk.instance.id"].create(
            {
                "instance_id": "test_instance_id",
                "odk_import_id": self.odk_import.id,
                "status": "pending",
            }
        )
        with patch.object(self.odk_config, "import_record_by_instance_id") as mock_import_record:
            mock_import_record.return_value = {"form_updated": True}
            self.odk_import._process_instance_id([instance_id])
        self.assertEqual(instance_id.status, "processing")

    def test_import_records_with_async(self):
        # Test importing records with async enabled
        self.odk_import.enable_async = True
        with patch.object(self.odk_config, "get_submissions") as mock_get_submissions:
            mock_get_submissions.return_value = [{"__id": "test_instance_id"}]
            self.odk_import.import_records()

        pending_instance = self.env["odk.instance.id"].search([("instance_id", "=", "test_instance_id")])
        self.assertTrue(pending_instance)
        self.assertEqual(pending_instance.status, "pending")

    def test_odk_import_action_trigger(self):
        # Test ODK import action trigger method
        self.odk_import.odk_import_action_trigger()
        self.assertEqual(self.odk_import.job_status, "running")
        self.assertTrue(self.odk_import.cron_id)

        self.odk_import.odk_import_action_trigger()
        self.assertEqual(self.odk_import.job_status, "completed")
        self.assertFalse(self.odk_import.cron_id)
