import base64
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestODKClient(TransactionCase):
    def setUp(self):
        super().setUp()
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
    def test_import_records_success(self, mock_get, mock_login):
        # Test importing delta records successfully
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "John Doe"}]}

        mock_login.return_value = "test_token"

        result = self.odk_config.import_records(self.json_formatter, self.target_registry)

        self.assertIn("value", result)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_records_with_timestamp(self, mock_get, mock_login):
        """Test importing records with a last sync timestamp"""
        # Mock the response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Test Name"}]}
        mock_login.return_value = "test_token"

        # Create a timestamp for testing
        test_timestamp = datetime(2024, 1, 1, 8, 0, 0)
        expected_filter = "__system/submissionDate ge 2024-01-01T08:00:00.000Z"

        # Call the method with timestamp
        self.odk_config.import_records(
            self.json_formatter, self.target_registry, last_sync_time=test_timestamp
        )

        # Verify the request was made with correct parameters
        actual_params = mock_get.call_args[1]["params"]
        self.assertIn("$filter", actual_params)
        self.assertEqual(actual_params["$filter"], expected_filter)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_records_without_timestamp(self, mock_get, mock_login):
        """Test importing records without a last sync timestamp"""
        # Mock the response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Test Name"}]}

        mock_login.return_value = "test_token"

        # Call the method without timestamp
        self.odk_config.import_records(self.json_formatter, self.target_registry)

        # Verify the request was made without filter parameter
        actual_params = mock_get.call_args[1]["params"]
        self.assertNotIn("$filter", actual_params)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_records_request_exception(self, mock_get, mock_login):
        """Test handling of RequestException during import"""
        mock_login.return_value = "test_token"
        # Simulate a request exception
        mock_get.side_effect = OSError("Network error")

        # Verify that ValidationError is raised with the correct message
        with self.assertRaises(ValidationError) as context:
            self.odk_config.import_records(self.json_formatter, self.target_registry)

            self.assertIn("Failed to parse response: Network error", str(context.exception))

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_records_with_skip(self, mock_get, mock_login):
        """Test importing records with skip parameter"""
        # Mock the response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Test Name"}]}

        mock_login.return_value = "test_token"

        # Call the method with skip parameter
        skip_value = 10
        self.odk_config.import_records(self.json_formatter, self.target_registry, skip=skip_value)

        # Verify the request was made with correct skip parameter
        actual_params = mock_get.call_args[1]["params"]
        self.assertEqual(actual_params["$skip"], skip_value)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_records_timestamp_and_skip(self, mock_get, mock_login):
        """Test importing records with both timestamp and skip parameters"""
        # Mock the response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Test Name"}]}

        mock_login.return_value = "test_token"

        test_timestamp = datetime(2024, 1, 1, 8, 0, 0)
        skip_value = 10
        expected_filter = "__system/submissionDate ge 2024-01-01T08:00:00.000Z"

        # Call the method with both parameters
        self.odk_config.import_records(
            self.json_formatter, self.target_registry, last_sync_time=test_timestamp, skip=skip_value
        )

        # Verify all parameters are correct
        actual_params = mock_get.call_args[1]["params"]
        self.assertEqual(actual_params["$skip"], skip_value)
        self.assertEqual(actual_params["$filter"], expected_filter)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_records_is_registrant(self, mock_get, mock_login):
        # Mock response for submissions
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Test Name"}]}

        mock_login.return_value = "test_token"

        # Set target_registry to "individual"
        self.target_registry = "individual"

        self.odk_config.import_records(self.json_formatter, self.target_registry)

        # Check if "is_registrant" and "is_group" were set correctly
        partner = self.env["res.partner"].search([], limit=1)
        self.assertTrue(partner.is_registrant)
        self.assertFalse(partner.is_group)

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_record_by_instance_id_is_registrant(self, mock_get, mock_login):
        # Mock response for submissions
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Doe John"}]}
        mock_login.return_value = "test_token"

        # Set target_registry to "individual"
        self.target_registry = "individual"

        self.odk_config.import_records(
            self.json_formatter, self.target_registry, instance_id="test_instance_id"
        )

        # Check if "is_registrant" and "is_group" were set correctly
        partner = self.env["res.partner"].search([], limit=1)
        self.assertTrue(partner.is_registrant)
        self.assertFalse(partner.is_group)
        self.assertEqual(partner.name, "Doe John")

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_record_by_instance_id_request_exception(self, mock_get, mock_login):
        """Test handling of IOError during import by instance ID"""
        mock_login.return_value = "test_token"
        # Simulate a network error
        mock_get.side_effect = OSError("Network error")

        instance_id = "test-instance-123"

        # Verify that ValidationError is raised with the correct message
        with self.assertRaises(ValidationError) as context:
            self.odk_config.import_records(self.json_formatter, self.target_registry, instance_id=instance_id)

            self.assertIn(
                "Failed to parse response by using instance ID: Network error",
                str(context.exception),
            )

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_record_by_instance_id_success(self, mock_get, mock_login):
        """Test successful import of record by instance ID with correct registry flags"""
        # Mock response data
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Doe John"}]}

        mock_login.return_value = "test_token"

        instance_id = "test-instance-123"
        # Test individual registry
        self.target_registry = "individual"

        result = self.odk_config.import_records(
            self.json_formatter, self.target_registry, instance_id=instance_id
        )

        # Verify the created partner data had correct flags
        partner = self.env["res.partner"].search([], limit=1)
        self.assertTrue(partner.is_registrant)
        self.assertFalse(partner.is_group)
        self.assertEqual(partner.name, "Doe John")
        self.assertTrue(result["form_updated"])

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("requests.get")
    def test_import_record_by_instance_id_group(self, mock_get, mock_login):
        """Test import of record by instance ID for group registry"""
        # Mock response data
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": [{"name": "Family Group"}]}

        instance_id = "test-instance-123"
        # Test group registry
        self.target_registry = "group"

        mock_login.return_value = "test_token"

        result = self.odk_config.import_records(
            self.json_formatter, self.target_registry, instance_id=instance_id
        )

        # Verify the created partner data had correct flags
        group = self.env["res.partner"].search([("is_group", "=", True)], limit=1)
        ind = self.env["res.partner"].search([("is_group", "=", False)], limit=1)
        self.assertTrue(group)
        self.assertTrue(ind)
        self.assertTrue(group.is_registrant)
        self.assertTrue(ind.is_registrant)
        self.assertEqual(group.name, "Family Group")
        self.assertTrue(result["form_updated"])

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.get_member_relationship")
    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.get_member_kind")
    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.get_individual_data")
    def test_handle_group_membership(self, mock_get_individual_data, mock_get_kind, mock_get_relationship):
        mock_relationship = {"source": 1, "relation": 3, "start_date": datetime.now()}
        mock_get_relationship.return_value = mock_relationship

        mock_kind_id = 2
        mock_get_kind.return_value.id = mock_kind_id

        mock_individual_data = {"name": "Test Person"}
        mock_get_individual_data.return_value = mock_individual_data

        # Test data
        mapped_json = {
            "group_membership_ids": [
                {"name": "Test Person", "kind": "member", "relationship_with_head": "spouse"}
            ]
        }

        self.odk_config.handle_one2many_fields(mapped_json, self.target_registry)

        # Verify individual creation
        partner = self.env["res.partner"].search([], limit=1)
        self.assertEqual(partner.name, mock_individual_data["name"])
        # self.assertEqual(partner.given_name, mock_individual_data["given_name"])
        # self.assertEqual(partner.family_name, mock_individual_data["family_name"])

        # Verify the results
        self.assertIn("group_membership_ids", mapped_json)
        self.assertIn("related_1_ids", mapped_json)

        # Verify relationship creation
        self.assertEqual(len(mapped_json["related_1_ids"]), 1)
        self.assertEqual(mapped_json["related_1_ids"][0][0], 0)
        self.assertEqual(mapped_json["related_1_ids"][0][1], 0)
        self.assertEqual(mapped_json["related_1_ids"][0][2], mock_relationship)

        # Verify group membership creation
        self.assertEqual(len(mapped_json["group_membership_ids"]), 1)
        expected_individual_data = {"individual": partner.id, "kind": [(4, mock_kind_id)]}
        self.assertEqual(mapped_json["group_membership_ids"][0][2], expected_individual_data)

    def test_handle_group_membership_no_relationship(self):
        # Test handling when no relationship is found
        mapped_json = {"group_membership_ids": [{"name": "Test Person"}]}

        self.odk_config.handle_one2many_fields(mapped_json, self.target_registry)

        ind = self.env["res.partner"].search([("is_group", "=", False)], limit=1)
        # Verify only group membership was created without relationship
        self.assertTrue("group_membership_ids" in mapped_json)
        self.assertEqual(len(mapped_json.get("related_1_ids", [])), 0)
        self.assertEqual(len(mapped_json["group_membership_ids"]), 1)
        expected_individual_data = {"individual": ind.id}
        self.assertEqual(mapped_json["group_membership_ids"][0][2], expected_individual_data)

    def test_handle_one2many_fields(self):
        # Create a mock environment with proper structure
        id_type = self.env["g2p.id.type"].create({"name": "National ID"})

        # Test data
        mapped_json = {
            "phone_number_ids": [
                {"phone_no": "123456789", "date_collected": "2024-07-01", "disabled": False}
            ],
            "group_membership_ids": [],
            "reg_ids": [{"id_type": "National ID", "value": "12345", "expiry_date": "2024-12-31"}],
        }

        # Execute
        self.odk_config.handle_one2many_fields(mapped_json, self.target_registry)

        # Assert phone_number_ids structure
        self.assertIn("phone_number_ids", mapped_json)
        self.assertEqual(len(mapped_json["phone_number_ids"]), 1)
        phone_data = mapped_json["phone_number_ids"][0]
        self.assertEqual(phone_data[0], 0)  # create command
        self.assertEqual(phone_data[1], 0)  # no id
        self.assertEqual(phone_data[2]["phone_no"], "123456789")
        self.assertEqual(phone_data[2]["date_collected"], "2024-07-01")
        self.assertEqual(phone_data[2]["disabled"], False)

        # Assert reg_ids structure
        self.assertIn("reg_ids", mapped_json)
        self.assertEqual(len(mapped_json["reg_ids"]), 1)
        reg_data = mapped_json["reg_ids"][0]
        self.assertEqual(reg_data[0], 0)  # create command
        self.assertEqual(reg_data[1], 0)  # no id
        self.assertEqual(reg_data[2]["id_type"], id_type.id)
        self.assertEqual(reg_data[2]["value"], "12345")
        self.assertEqual(reg_data[2]["expiry_date"], "2024-12-31")

    def test_handle_one2many_fields_no_id_type_found(self):
        # Test data
        mapped_json = {
            "reg_ids": [{"id_type": "NonExistent ID", "value": "12345", "expiry_date": "2024-12-31"}]
        }

        # Test should raise a ValidationError
        with self.assertRaises(ValidationError) as cm:
            self.odk_config.handle_one2many_fields(mapped_json, self.target_registry)

            self.assertIn("ID Type not found", str(cm.exception))

    def test_handle_one2many_fields_empty(self):
        """Test handling empty mapped_json"""
        mapped_json = {}
        self.odk_config.handle_one2many_fields(mapped_json, self.target_registry)
        self.assertEqual(mapped_json, {})

    def test_handle_one2many_fields_only_phone(self):
        """Test handling only phone numbers"""
        mapped_json = {
            "phone_number_ids": [{"phone_no": "123456789", "date_collected": "2024-07-01", "disabled": False}]
        }
        self.odk_config.handle_one2many_fields(mapped_json, self.target_registry)
        self.assertEqual(len(mapped_json["phone_number_ids"]), 1)
        self.assertEqual(mapped_json["phone_number_ids"][0][2]["phone_no"], "123456789")

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.download_attachment")
    def test_handle_media_import(self, mock_download_attach, mock_login):
        mock_login.return_value = "test_token"
        mock_download_attach.return_value = b"fake_image_data"

        # Test handling media imports
        member = {"meta": {"instanceID": "test_instance"}}
        mapped_json = {"image_1920": "test_image.jpg"}

        self.odk_config.handle_media_import(mapped_json, member)

        self.assertEqual(mapped_json["image_1920"], base64.b64encode(b"fake_image_data"))

    def test_handle_media_import_no_instance_id(self):
        # Test with missing instance_id
        member = {}
        mapped_json = {}
        self.odk_config.handle_media_import(mapped_json, member)
        self.assertEqual(mapped_json, {})  # No changes should be made

        member = {"meta": {}}  # No instanceID
        mapped_json = {}
        self.odk_config.handle_media_import(mapped_json, member)
        self.assertEqual(mapped_json, {})  # No changes should be made

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.login_get_session_token")
    def test_handle_media_import_no_attachments(self, mock_login):
        mock_login.return_value = "test_token"

        # Test with empty attachments
        member = {"meta": {"instanceID": "test_instance"}}
        mapped_json = {}

        self.odk_config.handle_media_import(mapped_json, member)
        self.assertEqual(mapped_json, {})  # No changes should be made

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
            self.assertIn("Unexpected response format", log.output[0])
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

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.get_dob")
    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.get_gender")
    def test_get_individual_data_success(self, mock_get_gender, mock_get_dob):
        mock_get_dob.return_value = "1990-01-01"
        mock_get_gender.return_value = "Male"

        # Test case for successful retrieval of individual data
        record = {"name": "John Doe", "gender": "Male"}

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

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.get_dob")
    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.get_gender")
    def test_get_individual_data_no_name(self, mock_get_gender, mock_get_dob):
        mock_get_dob.return_value = "1990-01-01"
        mock_get_gender.return_value = "Female"

        # Test case when no name is provided in the record
        record = {"gender": "Female"}

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

    def test_get_member_kind(self):
        # Test with existing kind
        with patch("odoo.models.Model.env") as mock_env:
            mock_kind = MagicMock()
            mock_env["g2p.group.membership.kind"].search.return_value = mock_kind

            record = {"kind": "member"}
            result = self.odk_config.get_member_kind(record)
            self.assertEqual(result, mock_kind)

        with patch("odoo.models.Model.env") as mock_env:
            mock_env["g2p.group.membership.kind"].search.return_value = None

            # Test with non-existent kind
            record = {"kind": "nonexistent"}
            result = self.odk_config.get_member_kind(record)
            self.assertFalse(result)

        # Test with no kind in record
        record = {}
        result = self.odk_config.get_member_kind(record)
        self.assertFalse(result)

    def test_get_member_relationship(self):
        # Test with existing relationship
        relationship = self.env["g2p.relationship"].create(
            {"name": "spouse", "name_inverse": "spouse", "source_type": "i", "destination_type": "i"}
        )

        source_id = 1
        record = {"relationship_with_head": "spouse"}
        result = self.odk_config.get_member_relationship(source_id, record)

        self.assertIsNotNone(result)
        self.assertEqual(result["source"], source_id)
        self.assertEqual(result["relation"], relationship.id)
        self.assertIsInstance(result["start_date"], datetime)

        # Test with non-existent relationship
        record = {"relationship_with_head": "nonexistent"}
        result = self.odk_config.get_member_relationship(source_id, record)
        self.assertIsNone(result)

        # Test with no relationship in record
        record = {}
        result = self.odk_config.get_member_relationship(source_id, record)
        self.assertIsNone(result)

    def test_get_gender(self):
        # Test with existing gender
        self.env["gender.type"].create({"code": "Male", "value": "male"})

        result = self.odk_config.get_gender("male")
        self.assertEqual(result, "Male")

        # Test with non-existent gender
        result = self.odk_config.get_gender("nonexistent")
        self.assertIsNone(result)

        # Test with None gender value
        result = self.odk_config.get_gender(None)
        self.assertIsNone(result)

    def test_get_dob(self):
        # Test getting date of birth from record
        record = {"birthdate": "2000-01-01", "age": 4}

        dob = self.odk_config.get_dob(record)
        self.assertEqual(dob, "2000-01-01")

        record = {"age": 4}
        dob = self.odk_config.get_dob(record)
        self.assertEqual(dob[:4], str(datetime.now().year - 4))

    def test_get_dob_future_birth_year(self):
        # Create a record with an age resulting in a birthdate one day in the future
        now = datetime.now()
        future_age = now.year - (now.year + 1) + 1  # Simulate age for birthdate exactly one day in the future
        record = {"age": int(future_age)}  # Ensure age is an integer

        # Call the method
        dob = self.odk_config.get_dob(record)

        # Verify the return value is None
        self.assertIsNone(dob)
