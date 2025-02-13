from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMTSConnector(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_queue_job_no_delay=True))

        cls.connector = cls.env["mts.connector"].create(
            {
                "name": "Test Connector",
                "mts_url": "http://test-mts.local",
                "input_type": "odk",
                "output_type": "json",
                "delivery_type": "callback",
                "is_recurring": "onetime",
                "callback_url": "http://callback.local",
                "callback_httpmethod": "POST",
                "callback_timeout": 10,
                "callback_authtype": "odoo",
                "callback_auth_database": "test_db",
                "callback_auth_url": "http://auth.local",
                "callback_auth_username": "test_user",
                "callback_auth_password": "test_pass",
                "odk_base_url": "http://odk.local",
                "odk_odata_url": "http://odk-odata.local",
                "odk_email": "test@example.com",
                "odk_password": "test_pass",
            }
        )

    def test_constraints(self):
        # Test all constrain methods
        future_time = datetime.now() + timedelta(days=1)
        past_time = datetime.now() - timedelta(days=1)

        with self.assertRaises(ValidationError):
            self.connector.write({"start_datetime": future_time})

        with self.assertRaises(ValidationError):
            self.connector.write({"start_datetime": past_time, "end_datetime": future_time})

        with self.assertRaises(ValidationError):
            self.connector.write({"mapping": "invalid json"})

        with self.assertRaises(ValidationError):
            self.connector.write({"output_format": "invalid jq"})

    @patch("odoo.addons.mts_connector.models.mts_connector.requests.post")
    def test_mts_onetime_action(self, mock_post):
        mock_post.return_value.text = "success"

        # Setting required datetime fields
        now = datetime.now()
        self.connector.write({"start_datetime": now - timedelta(minutes=5), "end_datetime": now})

        self.connector.mts_action_trigger()
        self.assertEqual(self.connector.job_status, "completed")

        self.connector.mts_onetime_action(self.connector.id)
        self.assertEqual(self.connector.job_status, "completed")

    def test_recurring_job(self):
        self.connector.write({"is_recurring": "recurring", "interval_minutes": 5})

        self.connector.mts_action_trigger()
        self.assertEqual(self.connector.job_status, "running")
        self.assertTrue(self.connector.cron_id)

        self.connector.mts_action_trigger()
        self.assertEqual(self.connector.job_status, "completed")
        self.assertFalse(self.connector.cron_id)

    def test_custom_input(self):
        # Test mts_onetime_action
        self.connector.write({"input_type": "custom"})
        self.connector.mts_onetime_action(self.connector.id)
        self.assertEqual(self.connector.input_type, "custom")
        self.assertEqual(self.connector.job_status, "completed")

    def test_datetime_to_iso(self):
        # Test iso to datetime conversion
        dt = datetime(2024, 1, 1, 12, 0, 0, 123456)
        iso_str = self.connector.datetime_to_iso(dt)
        self.assertEqual(iso_str, "2024-01-01T12:00:00.123Z")
