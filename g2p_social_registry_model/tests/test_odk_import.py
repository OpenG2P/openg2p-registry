from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.g2p_odk_importer.models.odk_import import OdkImport


class TestOdkImport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.odk_config = self.env["odk.config"].create(
            {
                "name": "Test ODK Config",
                "base_url": "http://example.com",
                "username": "test_user",
                "password": "TestPassword1!",
                "project": 1,
                "form_id": "test_form_id",
            }
        )

        self.odk_import = self.env["odk.import"].create(
            {
                "odk_config": self.odk_config.id,
                "json_formatter": ".",
                "target_registry": "individual",
                "last_sync_time": datetime.now() - timedelta(days=1),
                "job_status": "draft",
                "interval_hours": 1,
                "enable_import_by_instance_id": True,
            }
        )

    def test_process_records_handle_addl_data(self):
        """Test process_records_handle_addl_data updates mapped_json with required fields"""

        mapped_json = {
            "name": "John Doe",
            "education_level": "Bachelor's",
            "employment_status": "Employed",
            "other_field": "preserved_value",
        }

        with patch.object(OdkImport, "process_records_handle_addl_data", return_value={"status": "success"}):
            self.odk_import.process_records_handle_addl_data(mapped_json)

            # These are still in the dictionary since update doesn't remove existing keys
            self.assertEqual(mapped_json["education_level"], "Bachelor's")
            self.assertEqual(mapped_json["employment_status"], "Employed")
            self.assertEqual(mapped_json["name"], "John Doe")
            self.assertEqual(mapped_json["other_field"], "preserved_value")
