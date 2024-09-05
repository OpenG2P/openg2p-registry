from datetime import datetime
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from odoo.addons.g2p_odk_importer.models.odk_client import ODKClient


class TestODKClient(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env_mock = MagicMock()
        cls.base_url = "http://example.com"
        cls.username = "test_user"
        cls.password = "test_password"
        cls.project_id = 5
        cls.form_id = "test_form_id"
        cls.target_registry = "group"
        cls.json_formatter = "."
        cls.client = ODKClient(
            cls.env_mock,
            1,
            cls.base_url,
            cls.username,
            cls.password,
            cls.project_id,
            cls.form_id,
            cls.target_registry,
            cls.json_formatter,
        )

    @patch("requests.post")
    def test_login_success(self, mock_post):
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

    @patch("requests.get")
    def test_test_connection_success(self, mock_get):
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
    def test_import_delta_records_success(self, mock_get):
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
        member = {"meta": {"instanceID": "test_instance"}}
        mapped_json = {}
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"fake_image_data"
        mock_get.return_value.json.return_value = [{"name": "test_image.jpg"}]

        self.client.handle_media_import(member, mapped_json)
        self.assertIn("supporting_documents_ids", mapped_json)

    def test_get_dob(self):
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
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "full_name": "Test",
                }
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

        instance_id = "test_instance_id"
        result = odk_client.import_record_by_instance_id(instance_id)

        self.assertIn("form_updated", result)
        self.assertTrue(result["form_updated"])
