from datetime import datetime

from odoo.tests import TransactionCase


class TestG2PAuthIDOidcProvider(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test ID type, OAuth provider, partner, and registration ID
        cls.id_type = cls.env["g2p.id.type"].create({"name": "Test ID Type"})
        cls.auth_provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "Test OAuth Provider",
                "flow": "oauth2",
                "body": '{"en_US": "Log in with Test OAuth Provider"}',
                "client_id": "test-client-id",
                "client_authentication_method": "client_secret_post",
                "allow_signup": "yes",
                "g2p_self_service_allowed": True,
                "g2p_service_provider_allowed": False,
                "g2p_portal_oauth_callback_url": "http://test.callback.url",
                "sequence": 10,
                "company_id": 1,
                "create_uid": 1,
                "write_uid": 1,
                "auth_endpoint": "https://example.com/auth",
                "g2p_id_type": cls.id_type.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.reg_id = cls.env["g2p.reg.id"].create(
            {
                "partner_id": cls.partner.id,
                "id_type": cls.id_type.id,
                "value": "test123",
            }
        )

    def test_find_existing_partner_with_valid_id(self):
        """Test finding existing partner with valid ID"""
        validation = {"user_id": "test123"}
        result = self.auth_provider.oidc_signin_find_existing_partner(validation, {})
        self.assertEqual(result, self.partner)

    def test_find_existing_partner_with_invalid_id(self):
        """Test finding existing partner with invalid ID"""
        validation = {"user_id": "nonexistent"}
        result = self.auth_provider.oidc_signin_find_existing_partner(validation, {})
        self.assertIsNone(result)

    def test_process_name(self):
        """Test name processing"""
        validation = {"name": "John Middle Doe"}
        result = self.auth_provider.oidc_signin_process_name(validation, {})
        self.assertEqual(result["given_name"], "John")
        self.assertEqual(result["family_name"], "Doe")
        self.assertEqual(result["addl_name"], "Middle")
        self.assertEqual(result["name"], "DOE, JOHN MIDDLE")

    def test_process_name_without_middle(self):
        """Test name processing without middle name"""
        validation = {"name": "John Doe"}
        result = self.auth_provider.oidc_signin_process_name(validation, {})
        self.assertEqual(result["given_name"], "John")
        self.assertEqual(result["family_name"], "Doe")
        self.assertEqual(result["addl_name"], "")
        self.assertEqual(result["name"], "DOE, JOHN")

    def test_process_reg_ids_new_partner(self):
        """Test processing reg IDs for new partner"""
        validation = {"user_id": "new_id"}
        result = self.auth_provider.oidc_signin_process_reg_ids(validation, {})
        self.assertTrue(result["reg_ids"])
        new_reg = result["reg_ids"][0]
        self.assertEqual(new_reg[0], 0)  # Create command
        self.assertEqual(new_reg[2]["id_type"], self.id_type.id)
        self.assertEqual(new_reg[2]["value"], "new_id")

    def test_process_reg_ids_existing_partner(self):
        """Test processing reg IDs for existing partner"""
        validation = {"user_id": "updated_id"}
        result = self.auth_provider.oidc_signin_process_reg_ids(validation, {}, oauth_partner=self.partner)
        self.assertTrue(result["reg_ids"])
        updated_reg = result["reg_ids"][0]
        self.assertEqual(updated_reg[0], 1)  # Update command
        self.assertEqual(updated_reg[2]["value"], "updated_id")
        self.assertEqual(updated_reg[2]["authentication_status"], "authenticated")
        self.assertTrue(isinstance(updated_reg[2]["last_authentication_time"], datetime))

    def test_process_phone_new_partner(self):
        """Test processing phone for new partner"""
        validation = {"phone": "+1234567890"}
        result = self.auth_provider.oidc_signin_process_phone(validation, {})
        self.assertTrue(result["phone_number_ids"])
        new_phone = result["phone_number_ids"][0]
        self.assertEqual(new_phone[0], 0)  # Create command
        self.assertEqual(new_phone[2]["phone_no"], "+1234567890")

    def test_process_phone_existing_partner(self):
        """Test processing phone for existing partner with same number"""
        self.env["g2p.phone.number"].create(
            {
                "partner_id": self.partner.id,
                "phone_no": "+1234567890",
            }
        )
        validation = {"phone": "+1234567890"}
        result = self.auth_provider.oidc_signin_process_phone(validation, {}, oauth_partner=self.partner)
        self.assertFalse(result.get("phone"))
        self.assertFalse(result["phone_number_ids"])

    def test_process_other_fields(self):
        """Test processing other fields"""
        validation = {}
        result = self.auth_provider.oidc_signin_process_other_fields(validation, {})
        self.assertTrue(result["is_registrant"])
        self.assertFalse(result["is_group"])

    def test_multiple_user_ids(self):
        """Test processing multiple user IDs"""
        validation = {
            "user_id": "main_id",
            "user_id2": "second_id",
        }
        result = self.auth_provider.oidc_signin_process_reg_ids(validation, {})
        self.assertEqual(len(result["reg_ids"]), 2)
        id_values = [reg[2]["value"] for reg in result["reg_ids"]]
        self.assertIn("main_id", id_values)
        self.assertIn("second_id", id_values)
