from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestOdkImport(TransactionCase):
    def setUp(self):
        super().setUp()
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

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.import_records")
    def test_fetch_record_by_instance_id(self, mock_import_record):
        # Test fetch record by instance ID method
        mock_import_record.return_value = {"form_updated": True}

        self.odk_import.instance_id = "test_instance_id"
        result = self.odk_import.fetch_record_by_instance_id()

        self.assertEqual(result["params"]["type"], "success")

        self.odk_import.instance_id = False
        with self.assertRaises(UserError):
            self.odk_import.fetch_record_by_instance_id()

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.test_connection")
    def test_test_connection(self, mock_test_connection):
        mock_test_connection.return_value = True

        result = self.odk_import.test_connection()
        self.assertEqual(result["params"]["message"], "Tested successfully.")

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.import_records")
    def test_process_instance_id(self, mock_import_record):
        mock_import_record.return_value = {"form_updated": True}

        # Test processing instance ID method
        instance_id = self.env["odk.instance.id"].create(
            {
                "instance_id": "test_instance_id",
                "odk_import_id": self.odk_import.id,
                "status": "pending",
            }
        )
        self.odk_import._process_instance_id([instance_id])
        self.assertEqual(instance_id.status, "processing")

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.get_submissions")
    def test_import_records_with_async(self, mock_get_submissions):
        mock_get_submissions.return_value = [{"__id": "test_instance_id"}]

        # Test importing records with async enabled
        self.odk_import.enable_async = True
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

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.import_records")
    def test_import_records(self, mock_import_record):
        # Case 1: Successful import
        mock_import_record.return_value = {"form_updated": True, "partner_count": 5}

        result = self.odk_import.import_records()
        self.assertEqual(result["params"]["type"], "success")
        self.assertIn("5 records were imported successfully.", result["params"]["message"])

        # Case 2: Import failed
        mock_import_record.return_value = {"form_failed": True}
        result = self.odk_import.import_records()
        self.assertEqual(result["params"]["type"], "danger")
        self.assertIn("ODK form import failed", result["params"]["message"])

        # Case 3: No new records
        mock_import_record.return_value = {}
        result = self.odk_import.import_records()
        self.assertEqual(result["params"]["type"], "warning")
        self.assertIn("No new form records were submitted.", result["params"]["message"])

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.import_records")
    def test_odk_setting_disabled(self, mock_import_record):
        mock_import_record.return_value = None

        # Test when ODK setting is disabled
        self.odk_import.enable_import_by_instance_id = False
        with self.assertRaises(UserError):
            self.odk_import.fetch_record_by_instance_id()

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.import_records")
    def test_import_failed(self, mock_import_record):
        mock_import_record.return_value = {"form_failed": True}

        # Test when import fails
        self.odk_import.instance_id = "test_instance_id"

        result = self.odk_import.fetch_record_by_instance_id()

        self.assertEqual(result["params"]["type"], "danger")
        self.assertIn("ODK form import failed", result["params"]["message"])

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.import_records")
    def test_no_record_found(self, mock_import_record):
        mock_import_record.return_value = {}

        # Test when no record is found for the given instance ID
        self.odk_import.instance_id = "test_instance_id"

        result = self.odk_import.fetch_record_by_instance_id()

        self.assertEqual(result["params"]["type"], "warning")
        self.assertIn("No record found using this instance ID.", result["params"]["message"])

    def test_constraint_json_fields_invalid(self):
        # Test case: Invalid JSON formatter raises ValidationError
        with self.assertRaises(ValidationError):
            self.odk_import.json_formatter = "{ invalid_json: .value "  # Missing closing brace

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.import_records")
    def test_process_instance_id_exception(self, mock_import_record):
        mock_import_record.side_effect = Exception("Test Exception")

        # Create a test instance_id
        instance_id = self.env["odk.instance.id"].create(
            {
                "instance_id": "test_instance_id",
                "odk_import_id": self.odk_import.id,
                "status": "pending",
            }
        )

        # Process the instance_id and handle the exception
        with self.assertLogs(level="ERROR") as log:
            self.odk_import._process_instance_id([instance_id])

            # Verify logger was called with the exception details
            self.assertTrue(
                any("Failed to import instance ID test_instance_id" in log_out for log_out in log.output)
            )

        # Re-fetch the instance_id to check its updated status
        updated_instance_id = self.env["odk.instance.id"].browse(instance_id.id)

        # Check that the status was updated to "failed"
        self.assertEqual(updated_instance_id.status, "failed")
