from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestODKClient(TransactionCase):
    def setUp(self):
        super().setUp()
        self.odk_config = self.env["odk.config"].create(
            {
                "name": "Test Config",
                "base_url": "http://example.com",
                "username": "test_user",
                "password": "test_password",
                "project": 5,
                "form_id": "test_form_id",
            }
        )

    @patch("requests.post")
    def test_login_success(self, mock_post):
        # Test login success method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "test_token",
            "expiresAt": datetime.now(tz=timezone.utc).isoformat(),
        }
        mock_post.return_value = mock_response

        token = self.odk_config.login_get_session_token()
        self.assertEqual(token, "test_token")

    @patch("requests.post")
    def test_login_exception(self, mock_post):
        # Test login exception handling
        mock_post.side_effect = Exception("Network error")

        with self.assertRaises(ValidationError) as cm:
            self.odk_config.login_get_session_token()

        self.assertEqual(str(cm.exception), "Login failed: Network error")

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_test_connection_success(self, mock_get, mock_login):
        # Test successful connection
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"displayName": "test_user"}
        mock_get.return_value = mock_response

        mock_login.return_value = "test_token"
        test_connection = self.odk_config.test_connection()

        self.assertTrue(test_connection)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_connection_failure(self, mock_get, mock_login):
        # Test connection failure handling
        mock_get.side_effect = Exception("Connection error")
        mock_login.return_value = "test_token"

        with self.assertRaises(ValidationError) as cm:
            self.odk_config.test_connection()

            self.assertEqual(str(cm.exception), "Connection test failed: Connection error")

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_download_records_success(self, mock_get, mock_login):
        # Test importing delta records successfully
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "John Doe"}]}

        mock_login.return_value = "test_token"

        result = self.odk_config.download_records()

        actual_params = mock_get.call_args[1]["params"]
        # Verify the request was made without filter parameter
        self.assertNotIn("$filter", actual_params)
        self.assertIn("value", result)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_download_records_with_timestamp(self, mock_get, mock_login):
        """Test importing records with a last sync timestamp"""
        # Mock the response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Test Name"}]}
        mock_login.return_value = "test_token"

        # Create a timestamp for testing
        test_timestamp = datetime(2024, 1, 1, 8, 0, 0)
        expected_filter = "__system/submissionDate ge 2024-01-01T08:00:00.000Z"

        # Call the method with timestamp
        self.odk_config.download_records(last_sync_time=test_timestamp)

        # Verify the request was made with correct parameters
        actual_params = mock_get.call_args[1]["params"]
        self.assertIn("$filter", actual_params)
        self.assertEqual(actual_params["$filter"], expected_filter)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_download_records_request_exception(self, mock_get, mock_login):
        """Test handling of RequestException during import"""
        mock_login.return_value = "test_token"
        # Simulate a request exception
        mock_get.side_effect = OSError("Network error")

        # Verify that ValidationError is raised with the correct message
        with self.assertRaises(ValidationError) as context:
            self.odk_config.download_records()

            self.assertIn("Failed to parse response: Network error", str(context.exception))

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_download_records_with_skip(self, mock_get, mock_login):
        """Test importing records with skip parameter"""
        # Mock the response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Test Name"}]}

        mock_login.return_value = "test_token"

        # Call the method with skip parameter
        skip_value = 10
        self.odk_config.download_records(skip=skip_value)

        # Verify the request was made with correct skip parameter
        actual_params = mock_get.call_args[1]["params"]
        self.assertEqual(actual_params["$skip"], skip_value)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_download_records_timestamp_and_skip(self, mock_get, mock_login):
        """Test importing records with both timestamp and skip parameters"""
        # Mock the response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Test Name"}]}

        mock_login.return_value = "test_token"

        test_timestamp = datetime(2024, 1, 1, 8, 0, 0)
        skip_value = 10
        expected_filter = "__system/submissionDate ge 2024-01-01T08:00:00.000Z"

        # Call the method with both parameters
        self.odk_config.download_records(last_sync_time=test_timestamp, skip=skip_value)

        # Verify all parameters are correct
        actual_params = mock_get.call_args[1]["params"]
        self.assertEqual(actual_params["$skip"], skip_value)
        self.assertEqual(actual_params["$filter"], expected_filter)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_get_submissions_with_fields(self, mock_get, mock_login):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"field1": "value1"}]}

        mock_login.return_value = "test_token"

        fields = "field1,field2"

        submissions = self.odk_config.get_submissions(fields=fields)

        self.assertIn("$select", mock_get.call_args[1]["params"])
        self.assertEqual(mock_get.call_args[1]["params"]["$select"], fields)
        self.assertEqual(submissions[0]["field1"], "value1")

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_get_submissions_with_last_sync_time(self, mock_get, mock_login):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"id": 1}]}

        mock_login.return_value = "test_token"

        last_sync_time = datetime(2024, 12, 25, 10, 0, 0)
        expected_filter = "__system/submissionDate ge 2024-12-25T10:00:00.000Z"

        submissions = self.odk_config.get_submissions(last_sync_time=last_sync_time)

        self.assertIn("$filter", mock_get.call_args[1]["params"])
        self.assertEqual(mock_get.call_args[1]["params"]["$filter"], expected_filter)
        self.assertEqual(submissions[0]["id"], 1)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_get_submissions_invalid_response(self, mock_get, mock_login):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"field1": "value1"}]  # Not a dict

        mock_login.return_value = "test_token"

        with self.assertLogs(level="ERROR") as log:
            submissions = self.odk_config.get_submissions()
            self.assertTrue(any("Unexpected response format" in log_out for log_out in log.output))
            self.assertEqual(len(submissions), 0)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_get_submissions_success(self, mock_get, mock_login):
        # Test importing submission successfully
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "value": [
                {"id": 2, "field1": "value1", "field2": "value2"},
                {"id": 3, "field1": "value3", "field2": "value4"},
            ]
        }

        mock_login.return_value = "test_token"

        submissions = self.odk_config.get_submissions()

        self.assertEqual(submissions[0]["id"], 2)
        self.assertEqual(submissions[1]["id"], 3)
