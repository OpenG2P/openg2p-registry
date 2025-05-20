import hashlib
import hmac
import json
import time
from unittest.mock import patch

from odoo.tests import HttpCase, tagged


class TestRegIdOidcControllerCommon(HttpCase):
    """Common base class for OIDC controller tests with CSRF handling"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test ID type for registration
        cls.id_type = cls.env["g2p.id.type"].create(
            {
                "name": "Test ID Type",
            }
        )

        # Create a test OIDC provider with minimal required fields
        cls.auth_provider = cls.env["auth.oauth.provider"].create(
            {
                "name": "Test OIDC Provider",
                "body": '{"en_US": "Log in with Test OAuth Provider"}',
                "client_id": "test_client",
                "enabled": True,
                "validation_endpoint": "https://test.com/validate",
                "auth_endpoint": "https://test.com/auth",
                "scope": "openid",
                "css_class": "fa fa-fw fa-sign-in",
                "flow": "oidc_auth_code",
            }
        )

        # Create a test partner record
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create a test registration ID for the partner
        cls.reg_id = cls.env["g2p.reg.id"].create(
            {
                "partner_id": cls.partner.id,
                "id_type": cls.id_type.id,
                "value": "test123",
            }
        )

    def _get_csrf_token(self, time_limit=None):
        """Generate CSRF token to prevent cross-site request forgery attacks"""
        CSRF_TOKEN_SALT = 365 * 24 * 60 * 60  # 1 year expiry for CSRF token

        # Retrieve the database secret (used for hashing)
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret")

        # If no time_limit is provided, default to 1 year expiry
        max_ts = int(time.time() + (time_limit or CSRF_TOKEN_SALT))

        # Create the message to hash using session SID and expiration timestamp
        msg = f"{self.session.sid}{max_ts}".encode()

        # Hash the message with the database secret using HMAC and SHA1
        hm = hmac.new(secret.encode("ascii"), msg, hashlib.sha1).hexdigest()

        # Return the token as a concatenation of hash and timestamp
        return f"{hm}o{max_ts}"


@tagged("post_install", "-at_install")
class TestRegIdOidcController(TestRegIdOidcControllerCommon):
    """Test OIDC controller actions for authentication with various edge cases"""

    def setUp(self):
        super().setUp()
        # Authenticate as an admin user for testing
        self.authenticate("admin", "admin")

        # Set up base test parameters for CSRF token
        self.test_state = {
            "d": self.env.cr.dbname,  # Current database name
            "p": self.auth_provider.id,  # OIDC provider ID
            "reg_id": self.reg_id.id,  # Registration ID
        }

    def test_authenticate_success(self):
        """Test successful authentication flow using OIDC"""
        csrf_token = self._get_csrf_token()  # Generate CSRF token
        kw = {
            "state": json.dumps(self.test_state),  # Include test state
            "code": "test_code",  # Mock code
            "csrf_token": csrf_token,  # CSRF token to prevent CSRF attacks
        }

        # Create a new ID type for validation data
        new_id_type = self.env["g2p.id.type"].create(
            {
                "name": "Different Test ID Type",
            }
        )

        # Mock methods for OIDC provider
        with patch.multiple(
            type(self.auth_provider),
            flow="oidc_auth_code",  # Set the flow to OIDC authentication code
            oidc_get_tokens=lambda *args: None,  # Mock the token retrieval method
            oidc_get_validation_dict=lambda *args: {
                "user_id": "test123",
                "reg_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "different_id_123",  # Provide different ID value
                            "id_type": new_id_type.id,  # Use the new ID type
                        },
                    )
                ],
                "name": "Test User",  # Provide test user data
            },
            oidc_signin_generate_user_values=lambda *args, **kwargs: None,  # Mock user generation
        ):
            # Call the OIDC authentication endpoint
            response = self.url_open(
                "/auth_oauth/g2p_registry_id/authenticate",
                data=kw,
            )
            # Verify the response status code is 200 (success)
            self.assertEqual(response.status_code, 200)

    def test_authenticate_non_oidc_provider(self):
        """Test authentication with a non-OIDC provider"""
        csrf_token = self._get_csrf_token()
        kw = {
            "state": json.dumps(self.test_state),
            "code": "test_code",
            "csrf_token": csrf_token,
        }

        # Change the flow to a non-OIDC (OAuth) provider
        with patch.object(type(self.auth_provider), "flow", "oauth"):
            response = self.url_open(
                "/auth_oauth/g2p_registry_id/authenticate",
                data=kw,
            )

            # Assert the response status is 200 (success)
            self.assertEqual(response.status_code, 200)

    def test_authenticate_error_handling(self):
        """Test authentication error handling"""
        csrf_token = self._get_csrf_token()
        kw = {
            "state": json.dumps(self.test_state),
            "code": "test_code",
            "csrf_token": csrf_token,
        }

        # Simulate an error during token retrieval
        with patch.multiple(
            type(self.auth_provider),
            flow="oidc_auth_code",
            oidc_get_tokens=lambda *args: (_ for _ in ()).throw(Exception("Test error")),
        ):
            response = self.url_open(
                "/auth_oauth/g2p_registry_id/authenticate",
                data=kw,
            )

            # Assert the response status code is 200 (success), even with error handling
            self.assertEqual(response.status_code, 200)

    def test_authenticate_invalid_db(self):
        """Test authentication with an invalid database"""
        csrf_token = self._get_csrf_token()
        kw = {
            "state": json.dumps(
                {
                    "d": "invalid_db",  # Set invalid database name
                    "p": self.auth_provider.id,
                    "reg_id": self.reg_id.id,
                }
            ),
            "code": "test_code",
            "csrf_token": csrf_token,
        }

        # Attempt to authenticate with an invalid database
        response = self.url_open(
            "/auth_oauth/g2p_registry_id/authenticate",
            data=kw,
        )
        # Assert the response status code is 400 (bad request)
        self.assertEqual(response.status_code, 400)

    def test_authenticate_id_mismatch(self):
        """Test authentication with mismatched ID"""
        csrf_token = self._get_csrf_token()
        kw = {
            "state": json.dumps(self.test_state),
            "code": "test_code",
            "csrf_token": csrf_token,
        }

        # Simulate an ID mismatch during authentication
        with patch.multiple(
            type(self.auth_provider),
            flow="oidc_auth",
            oidc_get_tokens=lambda *args: None,
            oidc_get_validation_dict=lambda *args: {"user_id": "different_id"},  # Mismatched ID
            oidc_signin_generate_user_values=lambda *args, **kwargs: None,
        ):
            response = self.url_open(
                "/auth_oauth/g2p_registry_id/authenticate",
                data=kw,
            )

            # Assert the response status code is 200 (success)
            self.assertEqual(response.status_code, 200)

            # Invalidate the registration ID cache and check its status
            self.reg_id._invalidate_cache()
            self.assertEqual(
                self.reg_id.authentication_status,
                "not_authenticated",  # Status should be 'not_authenticated'
                "Authentication status should be not_authenticated",
            )
            self.assertEqual(
                self.reg_id.description,
                "ID value does not match",  # Description should indicate mismatch
                "Description should indicate ID mismatch",
            )
