import base64
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

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

        self.member = {
            "__system": {
                "submitterName": "Test Enumerator",
                "submitterId": "1",
                "submissionDate": "2024-05-01T12:00:00.000Z",
            }
        }

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.process_records")
    def test_fetch_record_by_instance_id(self, mock_get):
        # Test fetch record by instance ID method
        mock_get.return_value = {"form_updated": True}

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

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.process_records")
    def test_process_pending_instance_id(self, mock_process_records):
        mock_process_records.return_value = {"form_updated": True}

        # Test processing instance ID method
        instance_id = self.env["odk.instance.id"].create(
            {
                "instance_id": "test_instance_id",
                "odk_import_id": self.odk_import.id,
                "status": "pending",
            }
        )
        self.odk_import._process_pending_instance_id([instance_id])
        self.assertEqual(instance_id.status, "processing")

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.process_records")
    def test_process_pending_instance_id_exception(self, mock_process_records):
        mock_process_records.side_effect = Exception("Test Exception")

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
            self.odk_import._process_pending_instance_id([instance_id])

            # Verify logger was called with the exception details
            self.assertTrue(
                any("Failed to import instance ID test_instance_id" in log_out for log_out in log.output)
            )

        # Re-fetch the instance_id to check its updated status
        updated_instance_id = self.env["odk.instance.id"].browse(instance_id.id)

        # Check that the status was updated to "failed"
        self.assertEqual(updated_instance_id.status, "failed")

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

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.process_records")
    def test_import_records(self, mock_process_records):
        # Case 1: Successful import
        mock_process_records.return_value = {"form_updated": True, "partner_count": 5}

        result = self.odk_import.import_records()
        self.assertEqual(result["params"]["type"], "success")
        self.assertIn("5 records were imported successfully.", result["params"]["message"])

        # Case 2: Import failed
        mock_process_records.return_value = {"form_failed": True}
        result = self.odk_import.import_records()
        self.assertEqual(result["params"]["type"], "danger")
        self.assertIn("ODK form import failed", result["params"]["message"])

        # Case 3: No new records
        mock_process_records.return_value = {}
        result = self.odk_import.import_records()
        self.assertEqual(result["params"]["type"], "warning")
        self.assertIn("No new form records were submitted.", result["params"]["message"])

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.process_records")
    def test_odk_by_instance_id_disabled(self, mock_process_records):
        mock_process_records.return_value = None

        # Test when ODK setting is disabled
        self.odk_import.enable_import_by_instance_id = False
        with self.assertRaises(UserError):
            self.odk_import.fetch_record_by_instance_id()

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.process_records")
    def test_import_failed(self, mock_process_records):
        mock_process_records.return_value = {"form_failed": True}

        # Test when import fails
        self.odk_import.instance_id = "test_instance_id"

        result = self.odk_import.fetch_record_by_instance_id()

        self.assertEqual(result["params"]["type"], "danger")
        self.assertIn("ODK form import failed", result["params"]["message"])

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.process_records")
    def test_no_record_found(self, mock_process_records):
        mock_process_records.return_value = {}

        # Test when no record is found for the given instance ID
        self.odk_import.instance_id = "test_instance_id"

        result = self.odk_import.fetch_record_by_instance_id()

        self.assertEqual(result["params"]["type"], "warning")
        self.assertIn("No record found using this instance ID.", result["params"]["message"])

    def test_constraint_json_fields_invalid(self):
        # Test case: Invalid JSON formatter raises ValidationError
        with self.assertRaises(ValidationError):
            self.odk_import.json_formatter = "{ invalid_json: .value "  # Missing closing brace

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.download_records")
    def test_process_records_individual(self, mock_get):
        # Mock response data
        mock_get.return_value = {
            "value": [
                {
                    "name": "Test Name",
                    "__system": {
                        "submitterName": "User G 1",
                        "submitterId": "52",
                        "submissionDate": "2025-03-28T16:42:07.669Z",
                    },
                }
            ]
        }

        # Set target_registry to "individual"
        self.odk_import.target_registry = "individual"

        self.odk_import.json_formatter = "{name: .name}"

        result = self.odk_import.process_records()

        # Check if "is_registrant" and "is_group" were set correctly
        partner = self.env["res.partner"].search([("is_registrant", "=", True)], limit=1)
        self.assertTrue(partner.is_registrant)
        self.assertFalse(partner.is_group)
        self.assertEqual(partner.name, "Test Name")
        self.assertTrue(result["form_updated"])

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.download_records")
    def test_process_records_group(self, mock_get):
        """Test import of record by instance ID for group registry"""
        # Mock response data
        mock_get.return_value = {
            "value": [
                {
                    "name": "Family Group",
                    "__system": {
                        "submitterName": "User G 1",
                        "submitterId": "52",
                        "submissionDate": "2025-03-28T16:42:07.669Z",
                    },
                }
            ]
        }

        # Test group registry
        self.odk_import.target_registry = "group"

        self.odk_import.json_formatter = "{name: .name}"

        result = self.odk_import.process_records()

        # Verify the created partner data had correct flags
        group = self.env["res.partner"].search(
            [("is_registrant", "=", True), ("is_group", "=", True)], limit=1
        )
        self.assertTrue(group)
        self.assertTrue(group.is_registrant)
        self.assertEqual(group.name, "Family Group")
        self.assertTrue(result["form_updated"])

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.get_member_relationship")
    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.get_member_kind")
    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.get_individual_data")
    def test_handle_group_membership(self, mock_get_individual_data, mock_get_kind, mock_get_relationship):
        mock_relationship = {"source": 1, "relation": 3, "start_date": datetime.now()}
        mock_get_relationship.return_value = mock_relationship

        mock_kind_id = 2
        mock_get_kind.return_value.id = mock_kind_id

        mock_individual_data = {"name": "Test Person", "is_registrant": True, "is_group": False}
        mock_get_individual_data.return_value = mock_individual_data

        # Test data
        mapped_json = {
            "group_membership_ids": [
                {"name": "Test Person", "kind": "member", "relationship_with_head": "spouse"}
            ]
        }

        self.odk_import.target_registry = "group"
        self.odk_import.process_records_handle_one2many_fields(mapped_json, self.member)

        # Verify individual creation
        partner = self.env["res.partner"].search([("is_registrant", "=", True)], limit=1)
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

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.get_individual_data")
    def test_handle_group_membership_no_relationship(self, mock_get_individual_data):
        mock_get_individual_data.return_value = {
            "name": "Test Person",
            "is_registrant": True,
            "is_group": False,
        }

        # Test handling when no relationship is found
        mapped_json = {"group_membership_ids": [{"name": "Test Person"}]}

        self.odk_import.target_registry = "group"
        self.odk_import.process_records_handle_one2many_fields(mapped_json, self.member)

        ind = self.env["res.partner"].search(
            [("is_registrant", "=", True), ("is_group", "=", False)], limit=1
        )
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

        self.odk_import.target_registry = "group"
        # Execute
        self.odk_import.process_records_handle_one2many_fields(mapped_json, self.member)

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
            self.odk_import.process_records_handle_one2many_fields(mapped_json, self.member)

            self.assertIn("ID Type not found", str(cm.exception))

    def test_handle_one2many_fields_empty(self):
        """Test handling empty mapped_json"""
        mapped_json = {}
        self.odk_import.process_records_handle_one2many_fields(mapped_json, self.member)
        self.assertEqual(mapped_json, {})

    def test_handle_one2many_fields_only_phone(self):
        """Test handling only phone numbers"""
        mapped_json = {
            "phone_number_ids": [{"phone_no": "123456789", "date_collected": "2024-07-01", "disabled": False}]
        }
        self.odk_import.process_records_handle_one2many_fields(mapped_json, self.member)
        self.assertEqual(len(mapped_json["phone_number_ids"]), 1)
        self.assertEqual(mapped_json["phone_number_ids"][0][2]["phone_no"], "123456789")

    @patch("odoo.addons.g2p_odk_importer.models.odk_config.OdkConfig.download_attachment")
    def test_handle_media_import(self, mock_download_attach):
        mock_download_attach.return_value = b"fake_image_data"

        # Test handling media imports
        member = {"meta": {"instanceID": "test_instance"}}
        mapped_json = {"image_1920": "test_image.jpg"}

        self.odk_import.process_records_handle_media_import(mapped_json, member)

        expected_value = base64.b64encode(b"fake_image_data").decode("utf-8")
        self.assertEqual(mapped_json["image_1920"], expected_value)
        # Ensure the value is a string, not bytes
        self.assertIsInstance(mapped_json["image_1920"], str)

    def test_handle_media_import_no_instance_id(self):
        # Test with missing instance_id
        member = {}
        mapped_json = {}
        self.odk_import.process_records_handle_media_import(mapped_json, member)
        self.assertEqual(mapped_json, {})  # No changes should be made

        member = {"meta": {}}  # No instanceID
        mapped_json = {}
        self.odk_import.process_records_handle_media_import(mapped_json, member)
        self.assertEqual(mapped_json, {})  # No changes should be made

    def test_handle_media_import_no_attachments(self):
        # Test with empty attachments
        member = {"meta": {"instanceID": "test_instance"}}
        mapped_json = {}

        self.odk_import.process_records_handle_media_import(mapped_json, member)
        self.assertEqual(mapped_json, {})  # No changes should be made

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.get_dob")
    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.get_gender")
    def test_get_individual_data_success(self, mock_get_gender, mock_get_dob):
        mock_get_dob.return_value = "1990-01-01"
        mock_get_gender.return_value = "Male"

        # Test case for successful retrieval of individual data
        record = {"name": "John Doe", "gender": "Male"}

        individual_data = self.odk_import.get_individual_data(record)

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

    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.get_dob")
    @patch("odoo.addons.g2p_odk_importer.models.odk_import.OdkImport.get_gender")
    def test_get_individual_data_no_name(self, mock_get_gender, mock_get_dob):
        mock_get_dob.return_value = "1990-01-01"
        mock_get_gender.return_value = "Female"

        # Test case when no name is provided in the record
        record = {"gender": "Female"}

        individual_data = self.odk_import.get_individual_data(record)

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
            result = self.odk_import.get_member_kind(record)
            self.assertEqual(result, mock_kind)

        with patch("odoo.models.Model.env") as mock_env:
            mock_env["g2p.group.membership.kind"].search.return_value = None

            # Test with non-existent kind
            record = {"kind": "nonexistent"}
            result = self.odk_import.get_member_kind(record)
            self.assertFalse(result)

        # Test with no kind in record
        record = {}
        result = self.odk_import.get_member_kind(record)
        self.assertFalse(result)

    def test_get_member_relationship(self):
        # Test with existing relationship
        relationship = self.env["g2p.relationship"].create(
            {"name": "spouse", "name_inverse": "spouse", "source_type": "i", "destination_type": "i"}
        )

        source_id = 1
        record = {"relationship_with_head": "spouse"}
        result = self.odk_import.get_member_relationship(source_id, record)

        self.assertIsNotNone(result)
        self.assertEqual(result["source"], source_id)
        self.assertEqual(result["relation"], relationship.id)
        self.assertIsInstance(result["start_date"], datetime)

        # Test with non-existent relationship
        record = {"relationship_with_head": "nonexistent"}
        result = self.odk_import.get_member_relationship(source_id, record)
        self.assertIsNone(result)

        # Test with no relationship in record
        record = {}
        result = self.odk_import.get_member_relationship(source_id, record)
        self.assertIsNone(result)

    def test_get_gender(self):
        # Test with existing gender
        self.env["gender.type"].create({"code": "Male", "value": "male"})

        result = self.odk_import.get_gender("male")
        self.assertEqual(result, "Male")

        # Test with non-existent gender
        result = self.odk_import.get_gender("nonexistent")
        self.assertIsNone(result)

        # Test with None gender value
        result = self.odk_import.get_gender(None)
        self.assertIsNone(result)

    def test_get_dob(self):
        # Test getting date of birth from record
        record = {"birthdate": "2000-01-01", "age": 4}

        dob = self.odk_import.get_dob(record)
        self.assertEqual(dob, "2000-01-01")

        record = {"age": 4}
        dob = self.odk_import.get_dob(record)
        self.assertEqual(dob[:4], str(datetime.now().year - 4))

    def test_get_dob_future_birth_year(self):
        # Create a record with an age resulting in a birthdate one day in the future
        now = datetime.now()
        future_age = now.year - (now.year + 1) + 1  # Simulate age for birthdate exactly one day in the future
        record = {"age": int(future_age)}  # Ensure age is an integer

        # Call the method
        dob = self.odk_import.get_dob(record)

        # Verify the return value is None
        self.assertIsNone(dob)
