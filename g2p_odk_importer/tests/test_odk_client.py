import base64
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestODKClient(TransactionCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.target_registry = "group"
        self.json_formatter = "."
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

    @patch("requests.get")
    def test_test_connection_success(self, mock_get):
        # Test successful connection
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"displayName": "test_user"}
        mock_get.return_value = mock_response

        with patch.object(self.odk_config, "login_get_session_token") as mock_login:
            mock_login.return_value = "test_token"
            test_connection = self.odk_config.test_connection()

        self.assertTrue(test_connection)

    def test_connection_failure(self):
        # Test connection failure handling
        with (
            self.assertRaises(ValidationError) as cm,
            patch.object(self.odk_config, "login_get_session_token") as mock_login,
            patch("requests.get") as mock_response,
        ):
            mock_response.side_effect = Exception("Connection error")
            mock_login.return_value = "test_token"
            self.odk_config.test_connection()

        self.assertEqual(str(cm.exception), "Connection test failed: Connection error")

    @patch("requests.get")
    def test_import_delta_records_success(self, mock_get):
        # Test importing delta records successfully
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": [{"name": "John Doe"}]}
        mock_get.return_value = mock_response

        with patch.object(self.odk_config, "login_get_session_token") as mock_login:
            mock_login.return_value = "test_token"
            result = self.odk_config.import_delta_records(self.json_formatter, self.target_registry)

        self.assertIn("value", result)

    def test_handle_one2many_fields(self):
        # Test handling one2many fields in the mapped JSON
        mapped_json = {
            "phone_number_ids": [
                {"phone_no": "123456789", "date_collected": "2024-07-01", "disabled": False}
            ],
            "group_membership_ids": [],
            "reg_ids": [{"id_type": "National ID", "value": "12345", "expiry_date": "2024-12-31"}],
        }
        self.odk_config.handle_one2many_fields(mapped_json)
        self.assertIn("phone_number_ids", mapped_json)
        self.assertIn("reg_ids", mapped_json)

    def test_handle_media_import(self):
        # Test handling media imports
        member = {"meta": {"instanceID": "test_instance"}}
        mapped_json = {"image_1920": "test_image.jpg"}

        with (
            patch.object(self.odk_config, "login_get_session_token") as mock_login,
            patch.object(self.odk_config, "download_attachment") as mock_download_attach,
        ):
            mock_login.return_value = "test_token"
            mock_download_attach.return_value = b"fake_image_data"
            self.odk_config.handle_media_import(mapped_json, member)

        self.assertEqual(mapped_json["image_1920"], base64.b64encode(b"fake_image_data"))

    def test_get_dob(self):
        # Test getting date of birth from record
        record = {"birthdate": "2000-01-01", "age": 4}

        dob = self.odk_config.get_dob(record)
        self.assertEqual(dob, "2000-01-01")

        record = {"age": 4}
        dob = self.odk_config.get_dob(record)
        self.assertEqual(dob[:4], str(datetime.now().year - 4))

    @patch("requests.get")
    def test_import_record_by_instance_id_success(self, mock_get):
        # Test importing record by instance ID successfully
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": [{"family_name": "Test", "given_name": "1"}]}
        mock_get.return_value = mock_response

        instance_id = "test_instance_id"
        with patch.object(self.odk_config, "login_get_session_token") as mock_login:
            mock_login.return_value = "test_token"
            result = self.odk_config.import_record_by_instance_id(instance_id)

        self.assertIn("form_updated", result)
        self.assertTrue(result["form_updated"])

    @patch("requests.get")
    def test_get_submissions_success(self, mock_get):
        # Test importing submission successfully
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {"id": 2, "field1": "value1", "field2": "value2"},
                {"id": 3, "field1": "value3", "field2": "value4"},
            ]
        }
        mock_get.return_value = mock_response

        with patch.object(self.odk_config, "login_get_session_token") as mock_login:
            mock_login.return_value = "test_token"
            submissions = self.odk_config.get_submissions()

        self.assertEqual(submissions[0]["id"], 2)
        self.assertEqual(submissions[1]["id"], 3)

    def test_get_individual_data_success(self):
        # Test case for successful retrieval of individual data
        record = {"name": "John Doe", "gender": "Male"}

        with (
            patch.object(self.odk_config, "get_dob") as mock_get_dob,
            patch.object(self.odk_config, "get_gender") as mock_get_gender,
        ):
            mock_get_dob.return_value = "1990-01-01"
            mock_get_gender.return_value = "Male"

            individual_data = self.odk_config.get_individual_data(record)

            mock_get_dob.assert_called_once_with(record)
            mock_get_gender.assert_called_once_with("Male")

        self.assertEqual(individual_data["name"], "John Doe")
        self.assertEqual(individual_data["given_name"], "John")
        self.assertEqual(individual_data["family_name"], "Doe")
        self.assertEqual(individual_data["addl_name"], "")
        self.assertEqual(individual_data["is_registrant"], True)
        self.assertEqual(individual_data["is_group"], False)
        self.assertEqual(individual_data["birthdate"], "1990-01-01")
        self.assertEqual(individual_data["gender"], "Male")

    def test_get_individual_data_no_name(self):
        # Test case when no name is provided in the record
        record = {"gender": "Female"}

        with (
            patch.object(self.odk_config, "get_dob") as mock_get_dob,
            patch.object(self.odk_config, "get_gender") as mock_get_gender,
        ):
            mock_get_dob.return_value = "1990-01-01"
            mock_get_gender.return_value = "Female"

            individual_data = self.odk_config.get_individual_data(record)

            mock_get_dob.assert_called_once_with(record)
            mock_get_gender.assert_called_once_with("Female")

        self.assertEqual(individual_data["name"], None)
        self.assertEqual(individual_data["given_name"], None)
        self.assertEqual(individual_data["family_name"], None)
        self.assertEqual(individual_data["addl_name"], None)
        self.assertEqual(individual_data["is_registrant"], True)
        self.assertEqual(individual_data["is_group"], False)
        self.assertEqual(individual_data["birthdate"], "1990-01-01")
        self.assertEqual(individual_data["gender"], "Female")

    @patch("requests.get")
    def test_list_expected_attachments(self, mock_get):
        # Test listing expected attachments
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"name": "test.jpg"}]

        with patch.object(self.odk_config, "login_get_session_token") as mock_login:
            mock_login.return_value = "test_token"
            result = self.odk_config.list_expected_attachments("test_instance")
        self.assertEqual(result[0]["name"], "test.jpg")

    @patch("requests.get")
    def test_download_attachment(self, mock_get):
        # Test downloading attachment
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"fake_image_data"

        with patch.object(self.odk_config, "login_get_session_token") as mock_login:
            mock_login.return_value = "test_token"
            result = self.odk_config.download_attachment("test_instance", "test.jpg")
        self.assertEqual(result, b"fake_image_data")
