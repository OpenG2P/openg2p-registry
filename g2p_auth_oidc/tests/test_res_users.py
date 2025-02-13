from unittest.mock import MagicMock, patch

from jose import jwt

from odoo.tests import TransactionCase

from odoo.addons.g2p_auth_oidc.models.auth_oauth_provider import AuthOauthProvider
from odoo.addons.g2p_auth_oidc.models.res_users import ResUsers


class TestResUsers(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create test company
        cls.company = cls.env.ref("base.main_company")

        # Create test groups
        cls.group1 = cls.env["res.groups"].create({"name": "Test Group 1"})
        cls.group2 = cls.env["res.groups"].create({"name": "Test Group 2"})

        # Create test provider
        cls.provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "Test Provider",
                "client_id": "test_client_id",
                "body": '{"en_US": "Log in with Test OAuth Provider"}',
                "flow": "oidc_auth_code",
                "validation_endpoint": "https://test.com/userinfo",
                "token_endpoint": "https://test.com/token",
                "auth_endpoint": "https://test.com/auth",
                "scope": "openid profile email",
                "token_map": "sub:user_id name:name email:email",
                "company_id": cls.company.id,
            }
        )

        # Create test user with company_id
        cls.user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Test User",
                    "login": "test_user",
                    "oauth_provider_id": cls.provider.id,
                    "oauth_uid": "test_oauth_uid",
                    "company_id": cls.company.id,
                    "partner_id": cls.env["res.partner"]
                    .create(
                        {
                            "name": "Test User",
                            "company_id": cls.company.id,
                        }
                    )
                    .id,
                }
            )
        )

    def setUp(self):
        super().setUp()
        self.params = {
            "access_token": "test_access_token",
        }

    @patch("requests.get")
    def test_auth_oauth_rpc(self, mock_get):
        """Test OAuth RPC calls"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_get.return_value = mock_response

        # Test JWT response
        mock_response.headers = {"content-type": "application/jwt"}
        mock_response.text = jwt.encode({"test": "value"}, "secret")

        result = self.env["res.users"]._auth_oauth_rpc("https://test.com/endpoint", "test_token")
        self.assertEqual(result["test"], "value")

        # Test JSON response
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"test": "value"}

        result = self.env["res.users"]._auth_oauth_rpc("https://test.com/endpoint", "test_token")
        self.assertEqual(result["test"], "value")

        # Test bearer challenge response
        mock_response.headers = {"WWW-Authenticate": 'Bearer error="invalid_token"'}

        result = self.env["res.users"]._auth_oauth_rpc("https://test.com/endpoint", "test_token")
        self.assertEqual(result["error"], "invalid_token")

        # Test invalid response
        mock_response.headers = {}

        result = self.env["res.users"]._auth_oauth_rpc("https://test.com/endpoint", "test_token")
        self.assertEqual(result["error"], "invalid_request")

    def test_auth_oauth_signin_no_user(self):
        """Test signin attempt with non-existent user"""
        validation = {"user_id": "non_existent_uid", "name": "New User", "email": "new@example.com"}

        # Test with no_user_creation context
        result = (
            self.env["res.users"]
            .with_context(no_user_creation=True)
            ._auth_oauth_signin(self.provider.id, validation, self.params)
        )
        self.assertFalse(result)

    def test_auth_oauth_signin_existing_user(self):
        """Test signin with existing user"""
        validation = {"user_id": "test_oauth_uid", "name": "Test User Updated", "email": "test@example.com"}

        result = self.env["res.users"]._auth_oauth_signin(self.provider.id, validation, self.params)
        self.assertEqual(result, "test_user")
        self.assertEqual(self.user.oauth_access_token, "test_access_token")

    @patch.object(AuthOauthProvider, "oidc_get_tokens", return_value=("test_access_token", "test_id_token"))
    @patch.object(AuthOauthProvider, "oidc_get_validation_dict", return_value={"user_id": "test_oauth_uid"})
    @patch.object(ResUsers, "_auth_oauth_signin", return_value="test_user")
    def test_auth_oauth_oidc_flow(self, mock_signin, mock_validation, mock_tokens):
        """Test the OIDC auth_oauth flow"""
        result = self.env["res.users"].auth_oauth(self.provider.id, self.params)
        self.assertEqual(result, (self.env.cr.dbname, "test_user", "test_access_token"))
