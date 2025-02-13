from unittest.mock import patch

from odoo.tests import TransactionCase


class TestG2PRegId(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test auth provider
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
            }
        )

        # Create test ID type
        cls.id_type = cls.env["g2p.id.type"].create(
            {
                "name": "Test ID Type",
                "auth_oauth_provider_id": cls.auth_provider.id,
            }
        )

        # Create test partner
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create test reg ID
        cls.reg_id = cls.env["g2p.reg.id"].create(
            {
                "partner_id": cls.partner.id,
                "id_type": cls.id_type.id,
                "value": "test123",
            }
        )

    def test_auth_oauth_provider_related_field(self):
        """Test that auth_oauth_provider_id is correctly related to id_type.auth_oauth_provider_id"""
        self.assertEqual(
            self.reg_id.auth_oauth_provider_id,
            self.id_type.auth_oauth_provider_id,
            "auth_oauth_provider_id should match the provider set on id_type",
        )

    def test_get_auth_oauth_provider_with_provider(self):
        """Test get_auth_oauth_provider when auth provider exists"""
        # Mock the list_providers method to return test data
        test_params = {
            "auth_link": "http://test.com/__value__",
            "other_param": "test",
        }

        with patch.object(
            type(self.env["auth.oauth.provider"]),
            "list_providers",
            return_value=[test_params],
        ):
            result = self.reg_id.get_auth_oauth_provider(self.reg_id.id)

            self.assertIsNotNone(result, "Should return provider parameters")
            self.assertEqual(
                result["auth_link"],
                "http://test.com/test123",
                "Auth link should have __value__ replaced with reg_id value",
            )
            self.assertEqual(
                result["other_param"],
                "test",
                "Other parameters should be preserved",
            )

    def test_get_auth_oauth_provider_without_provider(self):
        """Test get_auth_oauth_provider when no auth provider exists"""
        # Create reg ID without auth provider
        reg_id_no_provider = self.env["g2p.reg.id"].create(
            {
                "partner_id": self.partner.id,
                "id_type": self.env["g2p.id.type"].create({"name": "No Provider Type"}).id,
                "value": "test456",
            }
        )

        result = reg_id_no_provider.get_auth_oauth_provider(reg_id_no_provider.id)
        self.assertIsNone(result, "Should return None when no auth provider exists")

    def test_authentication_status_default(self):
        """Test default authentication status"""
        self.assertEqual(
            self.reg_id.authentication_status,
            "not_authenticated",
            "Default authentication status should be 'not_authenticated'",
        )

    def test_authentication_fields(self):
        """Test authentication related fields exist"""
        self.assertIn(
            "authentication_status",
            self.reg_id._fields,
            "authentication_status field should exist",
        )
        self.assertIn(
            "last_authentication_time",
            self.reg_id._fields,
            "last_authentication_time field should exist",
        )
        self.assertIn(
            "last_authentication_user_id",
            self.reg_id._fields,
            "last_authentication_user_id field should exist",
        )
