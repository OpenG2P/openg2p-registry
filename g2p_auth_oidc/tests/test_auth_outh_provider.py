import base64
import json
import logging
from datetime import datetime
from unittest.mock import ANY, MagicMock, patch

from jose import jwt

from odoo.exceptions import AccessDenied
from odoo.tests import TransactionCase

from odoo.addons.auth_oauth.models.res_users import ResUsers as AuthOauthResUsers
from odoo.addons.auth_signup.models.res_users import ResUsers as AuthSignupResUsers
from odoo.addons.g2p_auth_oidc.models.auth_oauth_provider import AuthOauthProvider

_logger = logging.getLogger(__name__)


class TestAuthOauthProvider(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Set up the environment with a specific company context
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.env = cls.env(context=dict(cls.env.context, company_id=cls.company.id))

        # Create test groups
        cls.group1 = (
            cls.env["res.groups"].sudo().create({"name": "Test Group 1", "full_name": "test.group.1"})
        )
        cls.group2 = (
            cls.env["res.groups"].sudo().create({"name": "Test Group 2", "full_name": "test.group.2"})
        )

        # Create a base OAuth provider for testing
        cls.provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "Test Provider",
                "client_id": "test_client_id",
                "client_secret": "test_secret",
                "body": '{"en_US": "Log in with Test OAuth Provider"}',
                "auth_endpoint": "https://test.com/auth",
                "scope": "openid profile email",
                "validation_endpoint": "https://test.com/userinfo",
                "token_endpoint": "https://test.com/token",
                "jwks_uri": "https://test.com/jwks",
                "flow": "oidc_auth_code",
                "token_map": "sub:user_id name:name email:email",
                "company_id": cls.company.id,
                "enable_pkce": True,
                "code_verifier": "test_code_verifier",
                "verify_at_hash": True,
                "date_format": "%Y/%m/%d",
                "allow_signup": "yes",
                "signup_default_groups": [(6, 0, [cls.group1.id])],
                "sync_user_groups": "on_login",
                "extra_authorize_params": '{"extra":"param"}',
            }
        )

        cls.client_private_key = base64.b64encode(b"mock_private_key").decode("ascii")

        cls.params = {
            "access_token": "test_access_token",
            "id_token": "test_id_token",
            "code": "test_code",
            "state": json.dumps({"t": "test_token"}),
        }

    @patch("requests.get")
    @patch("jose.jwt.decode")
    def test_verify_tokens(self, mock_jwt_decode, mock_get):
        """Test token verification methods"""

        # Mock JWKS response
        mock_get.return_value = MagicMock()
        mock_get.return_value.json.return_value = {"keys": [{"kid": "test-key", "kty": "RSA"}]}

        mock_jwt_decode.return_value = {"sub": "test_user"}

        # Test verify_access_token
        self.provider.verify_access_token(self.params)
        mock_jwt_decode.assert_called_with("test_access_token", ANY, options={"verify_aud": False})

        # Test verify_id_token
        self.provider.verify_id_token(self.params)
        mock_jwt_decode.assert_called_with(
            "test_id_token",
            ANY,
            audience="test_client_id",
            access_token="test_access_token",
            options={"verify_at_hash": True, "verify_aud": False},
        )

    def test_oidc_get_response_type(self):
        """Test response type determination"""
        self.assertEqual(self.provider.oidc_get_response_type("oidc_auth_code"), "code")
        self.assertEqual(self.provider.oidc_get_response_type("oidc_implicit"), "id_token token")
        self.assertEqual(self.provider.oidc_get_response_type("oauth2"), "token")
        self.assertEqual(self.provider.oidc_get_response_type("unknown"), "token")

    def test_combine_tokens(self):
        """Test token combination methods"""
        token1 = jwt.encode({"claim1": "value1"}, "secret")
        token2 = jwt.encode({"claim2": "value2"}, "secret")

        # Test combine_tokens
        result = self.provider.combine_tokens(token1, token2)
        self.assertEqual(result["claim1"], "value1")
        self.assertEqual(result["claim2"], "value2")

        # Test combine_token_dicts
        dict1 = {"key1": "value1"}
        dict2 = {"key2": "value2"}
        result = self.provider.combine_token_dicts(dict1, dict2)
        self.assertEqual(result["key1"], "value1")
        self.assertEqual(result["key2"], "value2")

    @patch("requests.get")
    def test_oidc_get_jwks(self, mock_get):
        """Test JWKS retrieval with caching"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"keys": ["test_key"]}
        mock_get.return_value = mock_response

        # First call
        result1 = self.provider.oidc_get_jwks()
        self.assertEqual(result1, {"keys": ["test_key"]})

        # Second call should use cache
        result2 = self.provider.oidc_get_jwks()
        self.assertEqual(result2, {"keys": ["test_key"]})
        mock_get.assert_called_once()

    def test_map_validation_values(self):
        """Test validation value mapping"""
        validation = {"sub": "test_user", "name": "Test User", "email": "test@example.com", "extra": "value"}

        # Test specific mapping
        self.provider.token_map = "sub:user_id name:name email:email"
        result = self.provider.map_validation_values(validation, {})
        self.assertEqual(result["user_id"], "test_user")
        self.assertEqual(result["name"], "Test User")
        self.assertEqual(result["email"], "test@example.com")
        self.assertNotIn("extra", result)

        # Test wildcard mapping
        self.provider.token_map = "*:*"
        result = self.provider.map_validation_values(validation, {})
        self.assertEqual(result, validation)

    @patch("jose.jwt.encode")
    @patch("base64.b64decode")
    def test_oidc_create_private_key_jwt(self, mock_b64decode, mock_jwt_encode):
        # Mock the base64 decode and jwt.encode behavior
        mock_b64decode.return_value = b"mock_private_key"
        mock_jwt_encode.return_value = "mock_encoded_jwt"

        token = self.provider.oidc_create_private_key_jwt()
        mock_jwt_encode.assert_called_once()
        claims = mock_jwt_encode.call_args[0][0]  # First positional argument is the claims dictionary
        secret = mock_jwt_encode.call_args[0][1]  # Second positional argument is the secret
        algorithm = mock_jwt_encode.call_args[1]["algorithm"]  # Keyword argument for algorithm

        self.assertEqual(claims["iss"], self.provider.client_id)
        self.assertEqual(claims["sub"], self.provider.client_id)
        self.assertIn("exp", claims)
        self.assertIn("iat", claims)
        self.assertEqual(secret, b"mock_private_key")
        self.assertEqual(algorithm, "RS256")

        # Verify the method returns the mocked encoded JWT
        self.assertEqual(token, "mock_encoded_jwt")

    @patch("requests.get")
    @patch("jose.jwt.decode")
    @patch.object(
        AuthOauthProvider,
        "_oidc_get_tokens_auth_code_flow",
        return_value=("test_access_token", "test_id_token"),
    )
    @patch.object(
        AuthOauthProvider,
        "_oidc_get_tokens_implicit_flow",
        return_value=("test_access_token", "test_id_token"),
    )
    @patch.object(AuthOauthProvider, "oidc_create_private_key_jwt", return_value=("mock_token"))
    @patch.object(AuthOauthProvider, "verify_access_token")
    @patch.object(AuthOauthProvider, "verify_id_token")
    def test_oidc_get_tokens_success(
        self,
        mock_verify_id_token,
        mock_verify_access_token,
        mock_create_private,
        mock_implicit_flow,
        mock_auth_code_flow,
        mock_jwt_decode,
        mock_get,
    ):
        """Test successful token retrieval for oidc_auth_code flow"""
        # Mock the JWKS response
        mock_get.return_value = MagicMock()
        mock_get.return_value.json.return_value = {"keys": [{"kid": "test-key", "kty": "RSA"}]}

        # Test with OIDC Authorization Code Flow
        self.provider.flow = "oidc_auth_code"
        access_token, id_token = self.provider.oidc_get_tokens(self.params)

        self.assertEqual(access_token, "test_access_token")
        self.assertEqual(id_token, "test_id_token")

        # Test with OIDC Implicit Flow
        self.provider.flow = "oidc_implicit"
        access_token, id_token = self.provider.oidc_get_tokens(self.params)

        self.assertEqual(access_token, "test_access_token")
        self.assertEqual(id_token, "test_id_token")

    @patch("requests.post")
    @patch.object(AuthOauthProvider, "oidc_create_private_key_jwt", return_value="mock_private_key_jwt")
    def test_oidc_get_tokens_auth_code_flow_private_key_jwt(self, mock_create_private_key, mock_post):
        """Test _oidc_get_tokens_auth_code_flow with all methods patched"""

        # Mock the response from requests.post
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token", "id_token": "test_id_token"}

        # Ensure the mock_post returns the mock_response correctly
        mock_post.return_value = mock_response

        # Set the necessary provider attributes
        self.provider.client_authentication_method = "private_key_jwt"  # Example method
        self.provider.client_id = "test_client_id"
        self.provider.client_secret = "test_secret"
        self.provider.token_endpoint = "https://test.com/token"
        self.provider.enable_pkce = True
        self.provider.code_verifier = "test_code_verifier"

        # Prepare parameters
        params = {"code": "test_code"}

        access_token, id_token = self.provider._oidc_get_tokens_auth_code_flow(
            params, "https://test.com/token"
        )

        self.assertEqual(access_token, "test_access_token")
        self.assertEqual(id_token, "test_id_token")

    @patch("requests.post")
    def test_oidc_get_tokens_auth_code_flow_client_secret_basic(self, mock_post):
        """Test _oidc_get_tokens_auth_code_flow with all methods patched"""

        # Mock the response from requests.post
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token", "id_token": "test_id_token"}

        # Ensure the mock_post returns the mock_response correctly
        mock_post.return_value = mock_response

        # Set the necessary provider attributes
        self.provider.client_authentication_method = "client_secret_basic"  # Example method
        self.provider.client_id = "test_client_id"
        self.provider.client_secret = "test_secret"
        self.provider.token_endpoint = "https://test.com/token"
        self.provider.enable_pkce = True
        self.provider.code_verifier = "test_code_verifier"

        # Prepare parameters
        params = {"code": "test_code"}

        access_token, id_token = self.provider._oidc_get_tokens_auth_code_flow(
            params, "https://test.com/token"
        )

        self.assertEqual(access_token, "test_access_token")
        self.assertEqual(id_token, "test_id_token")

    @patch("requests.post")
    def test_oidc_get_tokens_auth_code_flow_client_secret_post(self, mock_post):
        """Test _oidc_get_tokens_auth_code_flow with all methods patched"""

        # Mock the response from requests.post
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token", "id_token": "test_id_token"}

        # Ensure the mock_post returns the mock_response correctly
        mock_post.return_value = mock_response

        # Set the necessary provider attributes
        self.provider.client_authentication_method = "client_secret_post"  # Example method
        self.provider.client_id = "test_client_id"
        self.provider.client_secret = "test_secret"
        self.provider.token_endpoint = "https://test.com/token"
        self.provider.enable_pkce = True
        self.provider.code_verifier = "test_code_verifier"

        # Prepare parameters
        params = {"code": "test_code"}

        access_token, id_token = self.provider._oidc_get_tokens_auth_code_flow(
            params, "https://test.com/token"
        )

        self.assertEqual(access_token, "test_access_token")
        self.assertEqual(id_token, "test_id_token")

    @patch("requests.post")
    def test_oidc_get_tokens_auth_code_flow_none(self, mock_post):
        """Test _oidc_get_tokens_auth_code_flow with all methods patched"""

        # Mock the response from requests.post
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token", "id_token": "test_id_token"}

        # Ensure the mock_post returns the mock_response correctly
        mock_post.return_value = mock_response

        # Set the necessary provider attributes
        self.provider.client_authentication_method = "none"  # Example method
        self.provider.client_id = "test_client_id"
        self.provider.client_secret = "test_secret"
        self.provider.token_endpoint = "https://test.com/token"
        self.provider.enable_pkce = True
        self.provider.code_verifier = "test_code_verifier"

        # Prepare parameters
        params = {"code": "test_code"}

        access_token, id_token = self.provider._oidc_get_tokens_auth_code_flow(
            params, "https://test.com/token"
        )

        self.assertEqual(access_token, "test_access_token")
        self.assertEqual(id_token, "test_id_token")

    @patch("jose.jwt.get_unverified_claims", side_effect=lambda token: {"claims": f"mock_claims_{token}"})
    @patch.object(AuthOauthProvider, "combine_token_dicts", return_value={"combined_token": "mock_combined"})
    @patch.object(
        AuthOauthProvider, "map_validation_values", return_value={"mapped_validation": "mock_mapped"}
    )
    @patch.object(
        AuthOauthResUsers, "_auth_oauth_validate", return_value={"validated_data": "mock_validation"}
    )
    def test_oidc_get_validation_dict(
        self, mock_validate, mock_map_validation_values, mock_combine_token_dicts, mock_get_unverified_claims
    ):
        """Test oidc_get_validation_dict with mocked dependencies and test user"""

        # Use the provider instance from the class setup
        provider = self.provider

        # Mock params
        params = {
            "access_token": "test_access_token",
            "id_token": "test_id_token",
        }

        # Call the method
        result = provider.oidc_get_validation_dict(params)

        # Verify _auth_oauth_validate was called correctly
        mock_validate.assert_called_once_with(provider.id, "test_access_token")

        # Verify combine_tokens was called correctly
        mock_combine_token_dicts.assert_called_once_with(
            {"claims": "mock_claims_test_access_token"},
            {"claims": "mock_claims_test_id_token"},
            {"validated_data": "mock_validation"},
        )

        # Verify map_validation_values was called correctly
        mock_map_validation_values.assert_called_once_with({"combined_token": "mock_combined"}, params)

        # Assert final output
        self.assertEqual(result, {"mapped_validation": "mock_mapped"})

    def test_oidc_signin_process_login(self):
        """Test login processing with different scenarios"""
        validation = {"user_id": "12345"}

        # Test with email
        validation["email"] = "test@example.com"
        result = self.provider.oidc_signin_process_login(validation.copy(), {})
        self.assertEqual(result["login"], "test@example.com")

        # Test without email
        validation.pop("email")
        result = self.provider.oidc_signin_process_login(validation.copy(), {})
        self.assertEqual(result["login"], f"provider_{self.provider.id}_user_12345")

    def test_oidc_signin_process_name(self):
        """Test name processing with different scenarios"""
        # Test with name already present
        validation = {"name": "John Doe"}
        result = self.provider.oidc_signin_process_name(validation.copy(), {})
        self.assertEqual(result["name"], "John Doe")

        # Test without name but with email
        validation = {"email": "john@example.com"}
        result = self.provider.oidc_signin_process_name(validation.copy(), {})
        self.assertEqual(result["name"], "john@example.com")

    def test_oidc_signin_process_gender(self):
        """Test gender processing"""
        # Test with valid gender
        validation = {"gender": "male"}
        result = self.provider.oidc_signin_process_gender(validation.copy(), {})
        self.assertEqual(result["gender"], "Male")

        # Test with empty gender
        validation = {"gender": ""}
        result = self.provider.oidc_signin_process_gender(validation.copy(), {})
        self.assertEqual(result["gender"], "")

        # Test without gender field
        validation = {}
        result = self.provider.oidc_signin_process_gender(validation.copy(), {})
        self.assertNotIn("gender", result)

    def test_oidc_signin_process_birthdate(self):
        """Test birthdate processing"""
        # Test with valid date
        validation = {"birthdate": "2000/01/01"}
        result = self.provider.oidc_signin_process_birthdate(validation.copy(), {})
        self.assertEqual(result["birthdate"].strftime("%Y/%m/%d"), "2000/01/01")

        # Test with empty birthdate
        validation = {"birthdate": ""}
        result = self.provider.oidc_signin_process_birthdate(validation.copy(), {})
        self.assertNotIn("birthdate", result)

        # Test without birthdate field
        validation = {}
        result = self.provider.oidc_signin_process_birthdate(validation.copy(), {})
        self.assertEqual(result, {})

    def test_oidc_signin_process_email(self):
        """Test email processing"""
        # Test with email
        validation = {"email": "test@example.com"}
        result = self.provider.oidc_signin_process_email(validation.copy(), {})
        self.assertEqual(result["email"], "test@example.com")

        # Test without email
        validation = {}
        result = self.provider.oidc_signin_process_email(validation.copy(), {})
        self.assertIsNone(result["email"])

    def test_oidc_signin_process_phone(self):
        """Test phone processing"""
        # Test basic phone processing (default implementation just returns validation)
        validation = {"phone": "+1234567890"}
        result = self.provider.oidc_signin_process_phone(validation.copy(), {})
        self.assertEqual(result, validation)

    def test_oidc_signin_process_groups(self):
        """Test groups processing with different scenarios"""
        # Ensure groups exist and are accessible
        self.assertTrue(self.group1.exists(), "Test Group 1 does not exist")
        self.assertTrue(self.group2.exists(), "Test Group 2 does not exist")

        # Print debug information
        _logger.info(f"Group1 ID: {self.group1.id}, full_name: {self.group1.full_name}")
        _logger.info(f"Group2 ID: {self.group2.id}, full_name: {self.group2.full_name}")

        # Test with groups_id using exact full_name from the group
        validation = {"groups_id": [self.group1.full_name, self.group2.full_name]}
        result = self.provider.with_context(test_mode=True).oidc_signin_process_groups(validation.copy(), {})

        self.assertIn("groups_id", result, "groups_id should be in result")
        group_commands = result.get("groups_id", [])
        _logger.info(f"Group commands for groups_id test: {group_commands}")

        self.assertTrue(
            any(cmd[0] == 4 and cmd[1] == self.group1.id for cmd in group_commands),
            f"Expected group1 {self.group1.id} ({self.group1.full_name}) in commands {group_commands}",
        )

        # Test with groups
        validation = {"groups": [self.group1.full_name]}
        result = self.provider.with_context(test_mode=True).oidc_signin_process_groups(validation.copy(), {})

        self.assertIn("groups_id", result, "groups_id should be in result")
        group_commands = result.get("groups_id", [])
        _logger.info(f"Group commands for groups test: {group_commands}")

        self.assertTrue(
            any(cmd[0] == 4 and cmd[1] == self.group1.id for cmd in group_commands),
            f"Expected group1 {self.group1.id} ({self.group1.full_name}) in commands {group_commands}",
        )

        # Test with roles
        validation = {"roles": [self.group2.full_name]}
        result = self.provider.with_context(test_mode=True).oidc_signin_process_groups(validation.copy(), {})

        self.assertIn("groups_id", result, "groups_id should be in result")
        group_commands = result.get("groups_id", [])
        _logger.info(f"Group commands for roles test: {group_commands}")

        self.assertTrue(
            any(cmd[0] == 4 and cmd[1] == self.group2.id for cmd in group_commands),
            f"Expected group2 {self.group2.id} ({self.group2.full_name}) in commands {group_commands}",
        )

        # Test with no group information
        validation = {}
        result = self.provider.oidc_signin_process_groups(validation.copy(), {})
        self.assertEqual(result, {})

    def test_oidc_signin_process_other_fields(self):
        """Test processing of other fields"""
        # Test with partner model
        validation = {
            "name": "Test User",
            "email": "test@example.com",
            "invalid_field": "should be removed",
            "company_id": 999,  # Should be overwritten with provider's company
            "user_id": "12345",  # Special field that should be kept
        }

        result = self.provider.oidc_signin_process_other_fields(
            validation.copy(), {}, oauth_partner=self.env["res.partner"].new()
        )

        # Check valid fields are kept
        self.assertIn("name", result)
        self.assertIn("email", result)
        self.assertIn("user_id", result)

        # Check invalid field is removed
        self.assertNotIn("invalid_field", result)

        # Check company_id is set to provider's company
        self.assertEqual(result["company_id"], self.company.id)

        # Test with user model
        validation = {"login": "testuser", "invalid_field": "should be removed", "company_id": 999}

        result = self.provider.oidc_signin_process_other_fields(
            validation.copy(), {}, oauth_user=self.env["res.users"].new()
        )

        # Check valid fields are kept
        self.assertIn("login", result)

        # Check invalid field is removed
        self.assertNotIn("invalid_field", result)

        # Check company_id is set to provider's company
        self.assertEqual(result["company_id"], self.company.id)

    @patch.object(AuthOauthProvider, "oidc_signin_generate_user_values")
    @patch.object(AuthOauthProvider, "oidc_signin_process_email")
    @patch.object(AuthOauthProvider, "oidc_signin_process_login")
    @patch.object(AuthOauthProvider, "oidc_signin_process_groups")
    @patch.object(AuthOauthProvider, "oidc_signin_find_existing_partner")
    @patch.object(AuthSignupResUsers, "signup")
    def test_oidc_signin_create_user(
        self,
        mock_signup,
        mock_find_partner,
        mock_process_groups,
        mock_process_login,
        mock_process_email,
        mock_generate_values,
    ):
        """Test user creation with different signup scenarios"""

        # Setup mock returns
        mock_process_email.side_effect = lambda v, *args, **kwargs: v
        mock_process_login.side_effect = lambda v, *args, **kwargs: v
        mock_process_groups.side_effect = lambda v, *args, **kwargs: v
        mock_find_partner.return_value = False
        mock_generate_values.side_effect = lambda v, *args, **kwargs: {
            "login": v.get("login", "testuser"),
            "name": v.get("name", "Test User"),
            "email": v.get("email", "test@example.com"),
            "oauth_provider_id": self.provider.id,
            "oauth_uid": v.get("user_id", 123),
            "oauth_access_token": "test_access_token",
            "active": True,
            "groups_id": v.get("groups_id", []),
            "company_id": self.company.id,
            "company_ids": [(6, 0, [self.company.id])],
        }

        # Test data with all required fields
        validation = {
            "user_id": 123,
            "name": "Test User",
            "email": "test@example.com",
            "login": "testuser",
            "company_id": self.company.id,
        }

        params = {
            "state": json.dumps({"t": "signup_token"}),
            "access_token": "test_access_token",
            "id_token": "test_id_token",
        }

        # Case 1: Test system_default signup
        self.provider.allow_signup = "system_default"
        mock_signup.return_value = ("testuser", "signup_token")

        login = self.provider.oidc_signin_create_user(validation.copy(), params)
        self.assertEqual(login, "testuser")
        mock_signup.assert_called_once()
        mock_generate_values.assert_called()
        mock_signup.reset_mock()
        mock_generate_values.reset_mock()

        # Case 2: Test signup denied (allow_signup = 'no')
        self.provider.allow_signup = "no"
        with self.assertRaises(AccessDenied) as context:
            self.provider.oidc_signin_create_user(validation.copy(), params)
        self.assertTrue("OIDC Signup failed!" in str(context.exception))

    @patch.object(AuthOauthProvider, "oidc_signin_process_email", return_value={"email": "test@example.com"})
    @patch.object(AuthOauthProvider, "oidc_signin_process_login", return_value={"login": "testuser"})
    @patch.object(AuthOauthProvider, "oidc_signin_process_groups", return_value={"groups_id": []})
    @patch.object(AuthOauthProvider, "oidc_signin_process_name", return_value={"name": "Test User"})
    @patch.object(AuthOauthProvider, "oidc_signin_process_gender", return_value={"gender": "Male"})
    @patch.object(
        AuthOauthProvider, "oidc_signin_process_birthdate", return_value={"birthdate": datetime(2000, 1, 1)}
    )
    @patch.object(AuthOauthProvider, "oidc_signin_process_phone", return_value={"phone": "+1234567890"})
    @patch.object(
        AuthOauthProvider,
        "oidc_signin_process_picture",
        side_effect=lambda validation, *args, **kwargs: validation,
    )
    @patch.object(AuthOauthProvider, "oidc_signin_process_other_fields", return_value={})
    def test_oidc_signin_generate_user_values(
        self,
        mock_process_other_fields,
        mock_process_picture,
        mock_process_phone,
        mock_process_birthdate,
        mock_process_gender,
        mock_process_name,
        mock_process_groups,
        mock_process_login,
        mock_process_email,
    ):
        """Test oidc_signin_generate_user_values method"""
        validation = {
            "user_id": "12345",
            "email": "test@example.com",
            "name": "Test User",
            "gender": "male",
            "birthdate": "2000/01/01",
            "phone": "+1234567890",
            "picture": "https://test.com/picture.jpg",
        }
        params = {"access_token": "test_access_token"}
        result = self.provider.oidc_signin_generate_user_values(validation.copy(), params)

        # Verify the results
        # self.assertIn("login", result)
        self.assertIn("name", result)
        self.assertIn("gender", result)
        self.assertIn("birthdate", result)
        self.assertIn("phone", result)
        self.assertIn("picture", result)  # Picture URL should remain in the validation dict

    @patch.object(AuthOauthProvider, "oidc_signin_generate_user_values")
    def test_oidc_signin_update_userinfo(self, mock_generate_values):
        """Test user info update functionality"""
        # Create a test partner with sudo
        partner = (
            self.env["res.partner"]
            .sudo()
            .create(
                {
                    "name": "Test Partner",
                    "email": "test@example.com",
                    "company_id": self.company.id,
                }
            )
        )

        # Create test user with the existing partner
        user = (
            self.env["res.users"]
            .sudo()
            .with_context(no_reset_password=True, company_id=self.company.id)
            .create(
                {
                    "login": "testuser",
                    "partner_id": partner.id,
                    "company_id": self.company.id,
                    "oidc_userinfo_reset": True,
                }
            )
        )

        # Mock the generate_user_values method
        mock_generate_values.return_value = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "user_id": "12345",
        }

        # Test data
        validation = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "user_id": "12345",
        }

        # Test update when reset flag is True
        self.provider.oidc_signin_update_userinfo(validation, {}, oauth_partner=partner, oauth_user=user)

        # Verify mock was called correctly
        mock_generate_values.assert_called_once_with(
            validation, {}, oauth_partner=partner, oauth_user=user, create_user=False
        )

        # Verify partner data was updated
        self.assertEqual(partner.name, "Updated Name")
        self.assertEqual(partner.email, "updated@example.com")
        self.assertFalse(user.oidc_userinfo_reset)

        # Reset mock for next test
        mock_generate_values.reset_mock()

        # Test update when reset flag is False
        user.oidc_userinfo_reset = False
        validation["name"] = "Another Name"

        self.provider.oidc_signin_update_userinfo(validation, {}, oauth_partner=partner, oauth_user=user)

        # Verify mock was not called when reset is False
        mock_generate_values.assert_not_called()

        # Verify no changes were made.
        self.assertEqual(partner.name, "Updated Name")
        self.assertEqual(partner.email, "updated@example.com")

    @patch.object(AuthOauthProvider, "oidc_signin_process_groups")
    def test_oidc_signin_update_groups(self, mock_process_groups):
        """Test group update functionality"""
        # Create partner first with sudo
        partner = (
            self.env["res.partner"]
            .sudo()
            .create(
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    "company_id": self.company.id,
                }
            )
        )

        # Create user with the existing partner
        user = (
            self.env["res.users"]
            .sudo()
            .with_context(no_reset_password=True, company_id=self.company.id)
            .create(
                {
                    "login": "testuser",
                    "name": "Test User",
                    "partner_id": partner.id,
                    "company_id": self.company.id,
                    "oidc_groups_reset": True,
                }
            )
        )

        # Mock the process_groups method
        mock_process_groups.return_value = {"groups_id": [(4, self.group1.id), (4, self.group2.id)]}

        # Test data
        validation = {"groups_id": [(4, self.group1.id), (4, self.group2.id)]}

        # Test update when sync is 'on_login'
        self.provider.sync_user_groups = "on_login"
        self.provider.oidc_signin_update_groups(validation, {}, oauth_user=user)

        # Verify mock was called
        mock_process_groups.assert_called_once_with(validation, {}, oauth_partner=None, oauth_user=user)

        self.assertIn(self.group1, user.groups_id)
        self.assertIn(self.group2, user.groups_id)
        self.assertFalse(user.oidc_groups_reset)

        # Reset mock for next test
        mock_process_groups.reset_mock()

        # Test update when sync is 'on_reset' and reset flag is True
        user.groups_id = [(5, 0, 0)]  # Remove all groups
        user.oidc_groups_reset = True
        self.provider.sync_user_groups = "on_reset"

        self.provider.oidc_signin_update_groups(validation, {}, oauth_user=user)

        # Verify mock was called
        mock_process_groups.assert_called_once_with(validation, {}, oauth_partner=None, oauth_user=user)

        self.assertIn(self.group1, user.groups_id)
        self.assertIn(self.group2, user.groups_id)
        self.assertFalse(user.oidc_groups_reset)

        # Reset mock for next test
        mock_process_groups.reset_mock()

        # Test update when sync is 'never'
        user.groups_id = [(5, 0, 0)]  # Remove all groups
        self.provider.sync_user_groups = "never"

        self.provider.oidc_signin_update_groups(validation, {}, oauth_user=user)

        # Verify mock was not called when sync is 'never'
        mock_process_groups.assert_not_called()

        self.assertNotIn(self.group1, user.groups_id)
        self.assertNotIn(self.group2, user.groups_id)

    def test_list_providers(self):
        """Test that list_providers method works with various parameters"""

        # Test with basic parameters
        result = self.provider.list_providers(
            base_url="https://test.example.com", redirect="/web", db_name="test_db"
        )
        self.assertEqual(len(result), 1, "Should return one provider")

        # Test with additional keyword arguments
        result = self.provider.list_providers(
            base_url="https://test.example.com",
            redirect="/web",
            db_name="test_db",
            prompt="login",  # Additional parameter
            login_hint="user@example.com",  # Additional parameter
            custom_param="test_value",  # Custom parameter
        )

        self.assertTrue(result, "Method should return providers")
        self.assertEqual(len(result), 1, "Should return one provider")

        provider_oidc_flow = self.env["auth.oauth.provider"].create(
            {
                "name": "Test Provider",
                "client_id": "test_client_id",
                "client_secret": "test_secret",
                "body": '{"en_US": "Log in with Test OAuth Provider"}',
                "auth_endpoint": "https://test.com/auth",
                "scope": "openid profile email",
                "validation_endpoint": "https://test.com/userinfo",
                "token_endpoint": "https://test.com/token",
                "jwks_uri": "https://test.com/jwks",
                "flow": "oidc_auth_code",
                "token_map": "sub:user_id name:name email:email",
                "company_id": self.company.id,
                "enable_pkce": True,
                "code_verifier": "test_code_verifier",
                "verify_at_hash": True,
                "date_format": "%Y/%m/%d",
                "allow_signup": "yes",
                "signup_default_groups": [(6, 0, [self.group1.id])],
                "sync_user_groups": "on_login",
                "extra_authorize_params": '{"extra":"param"}',
            }
        )
        # Test with additional keyword arguments
        result = provider_oidc_flow.list_providers(
            base_url="https://test.example.com",
            redirect="/web",
            db_name="test_db",
            prompt="login",  # Additional parameter
            login_hint="user@example.com",  # Additional parameter
            custom_param="test_value",  # Custom parameter
        )
