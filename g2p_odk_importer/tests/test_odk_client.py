from datetime import datetime
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.g2p_odk_importer.models.odk_client import ODKClient


class TestODKClient(TransactionCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.env_mock = MagicMock()
        self.base_url = "http://example.com"
        self.username = "test_user"
        self.password = "test_password"
        self.project_id = 5
        self.form_id = "test_form_id"
        self.target_registry = "group"
        self.json_formatter = "."
        self.client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

    @patch("requests.post")
    def test_login_success(self, mock_post):
        # Test login success method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "test_token"}
        mock_post.return_value = mock_response

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        odk_client.login()
        self.assertEqual(odk_client.session, "test_token")

    @patch("requests.post")
    def test_login_exception(self, mock_post):
        # Test login exception handling
        mock_post.side_effect = Exception("Network error")

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        with self.assertRaises(ValidationError) as cm:
            odk_client.login()

        self.assertEqual(str(cm.exception), "Login failed: Network error")

    @patch("requests.get")
    def test_test_connection_success(self, mock_get):
        # Test successful connection
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"displayName": "test_user"}
        mock_get.return_value = mock_response

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        odk_client.session = "test_token"
        self.assertTrue(odk_client.test_connection())

    @patch("requests.get")
    def test_connection_no_session(self, mock_get):
        # Test connection when session is not created
        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        odk_client.session = None

        with self.assertRaises(ValidationError) as cm:
            odk_client.test_connection()

        self.assertEqual(str(cm.exception), "Session not created")

    @patch("requests.get")
    def test_connection_failure(self, mock_get):
        # Test connection failure handling
        mock_get.side_effect = Exception("Connection error")

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        odk_client.session = "valid_session_token"

        with self.assertRaises(ValidationError) as cm:
            odk_client.test_connection()

        self.assertEqual(str(cm.exception), "Connection test failed: Connection error")

    @patch("requests.get")
    def test_import_delta_records_success(self, mock_get):
        # Test importing delta records successfully
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": [{"name": "John Doe"}]}
        mock_get.return_value = mock_response

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        odk_client.session = "test_token"
        result = odk_client.import_delta_records()
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
        self.client.handle_one2many_fields(mapped_json)
        self.assertIn("phone_number_ids", mapped_json)
        self.assertIn("reg_ids", mapped_json)

    @patch("requests.get")
    def test_handle_media_import(self, mock_get):
        # Test handling media imports
        member = {"meta": {"instanceID": "test_instance"}}
        mapped_json = {}
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"fake_image_data"
        mock_get.return_value.json.return_value = [{"name": "test_image.jpg"}]

        self.client.handle_media_import(member, mapped_json)
        self.assertIn("supporting_documents_ids", mapped_json)

    def test_get_dob(self):
        # Test getting date of birth from record
        record = {"birthdate": "2000-01-01", "age": 4}
        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        dob = odk_client.get_dob(record)
        self.assertEqual(dob, "2000-01-01")

        record = {"age": 4}
        dob = odk_client.get_dob(record)
        self.assertEqual(dob[:4], str(datetime.now().year - 4))

    def test_is_image(self):
        # Test checking if file is an image
        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        result = odk_client.is_image("test.jpg")
        self.assertTrue(result)

    @patch("requests.get")
    def test_list_expected_attachments(self, mock_get):
        # Test listing expected attachments
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"name": "test.jpg"}]

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        result = odk_client.list_expected_attachments(
            "http://example.com", "1", "1", "test_instance", "fake_token"
        )
        self.assertIn({"name": "test.jpg"}, result)

    @patch("requests.get")
    def test_download_attachment(self, mock_get):
        # Test downloading attachment
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"fake_image_data"

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        result = odk_client.download_attachment(
            "http://example.com", "1", "1", "test_instance", "test.jpg", "fake_token"
        )
        self.assertEqual(result, b"fake_image_data")

    @patch("requests.get")
    def test_import_record_by_instance_id_success(self, mock_get):
        # Test importing record by instance ID successfully
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": [{"family_name": "Test", "given_name": "1"}]}
        mock_get.return_value = mock_response

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        instance_id = "test_instance_id"
        result = odk_client.import_record_by_instance_id(instance_id)

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

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        submissions = odk_client.get_submissions()

        self.assertEqual(submissions[0]["id"], 2)
        self.assertEqual(submissions[1]["id"], 3)

    @patch("odoo.addons.g2p_odk_importer.models.odk_client.ODKClient.get_dob")
    @patch("odoo.addons.g2p_odk_importer.models.odk_client.ODKClient.get_gender")
    def test_get_individual_data_success(self, mock_get_gender, mock_get_dob):
        # Test case for successful retrieval of individual data
        mock_get_dob.return_value = "1990-01-01"
        mock_get_gender.return_value = "Male"

        record = {"name": "John Doe", "gender": "Male"}

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        individual_data = odk_client.get_individual_data(record)

        self.assertEqual(individual_data["name"], "John Doe")
        self.assertEqual(individual_data["given_name"], "John")
        self.assertEqual(individual_data["family_name"], "Doe")
        self.assertEqual(individual_data["addl_name"], "")
        self.assertEqual(individual_data["is_registrant"], True)
        self.assertEqual(individual_data["is_group"], False)
        self.assertEqual(individual_data["birthdate"], "1990-01-01")
        self.assertEqual(individual_data["gender"], "Male")

        mock_get_dob.assert_called_once_with(record)
        mock_get_gender.assert_called_once_with("Male")

    @patch("odoo.addons.g2p_odk_importer.models.odk_client.ODKClient.get_dob")
    @patch("odoo.addons.g2p_odk_importer.models.odk_client.ODKClient.get_gender")
    def test_get_individual_data_no_name(self, mock_get_gender, mock_get_dob):
        # Test case when no name is provided in the record
        mock_get_dob.return_value = "1990-01-01"
        mock_get_gender.return_value = "Female"

        record = {"gender": "Female"}

        odk_client = ODKClient(
            self.env_mock,
            1,
            self.base_url,
            self.username,
            self.password,
            self.project_id,
            self.form_id,
            self.target_registry,
            self.json_formatter,
        )

        individual_data = odk_client.get_individual_data(record)

        self.assertEqual(individual_data["name"], None)
        self.assertEqual(individual_data["given_name"], None)
        self.assertEqual(individual_data["family_name"], None)
        self.assertEqual(individual_data["addl_name"], None)
        self.assertEqual(individual_data["is_registrant"], True)
        self.assertEqual(individual_data["is_group"], False)
        self.assertEqual(individual_data["birthdate"], "1990-01-01")
        self.assertEqual(individual_data["gender"], "Female")

        mock_get_dob.assert_called_once_with(record)
        mock_get_gender.assert_called_once_with("Female")
