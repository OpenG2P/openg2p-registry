from unittest.mock import MagicMock, patch

from odoo.exceptions import AccessDenied
from odoo.tests import TransactionCase

from odoo.addons.g2p_registry_theme import models


class TestResUser(TransactionCase):
    def setUp(self):
        """Set up test users."""
        super().setUp()
        self.user_model = self.env["res.users"]
        self.valid_user = self.user_model.create(
            {
                "name": "Valid User",
                "login": "abbb6166@gmail.com",
                "email": "abbb6166@gmail.com",
                "password": "AgentUser1!",
                "active": True,
            }
        )
        self.valid_user.partner_id.write({"is_registrant": False})
        user_group = self.env.ref("base.group_user")
        self.valid_user.groups_id = [(4, user_group.id)]
        self.invalid_user = self.user_model.create(
            {
                "name": "Invalid User",
                "login": "invalid_user@example.com",
                "email": "invalid_user@example.com",
                "password": "AgentUser1!",
                "active": True,
            }
        )
        self.registrant_user = self.user_model.create(
            {
                "name": "Registrant User",
                "login": "registrant_user@example.com",
                "email": "registrant_user@example.com",
                "password": "AgentUser1!",
                "active": True,
            }
        )
        self.registrant_user.partner_id.write({"is_registrant": True})

    def test_reset_password_invalid_user(self):
        """Test that an exception is raised when resetting password for an invalid user."""
        with self.assertRaises(Exception) as context:
            self.invalid_user.reset_password("non_existent@example.com")
        self.assertEqual(
            str(context.exception), "Incorrect email. Please enter the registered email address."
        )

    @patch("odoo.addons.g2p_registry_theme.models.res_user.ResUser.reset_password")
    def test_reset_password_valid_user(self, mock_action_reset_password):
        """Test that the password reset is triggered for a valid user."""
        self.valid_user.reset_password("abbb6166@gmail.com")
        mock_action_reset_password.assert_called_once()

    def test_login_access_denied_for_registrant(self):
        """Test that a registrant user is denied access."""
        mock_request = MagicMock()
        mock_httprequest = MagicMock()
        mock_httprequest.path = "/web/login"
        mock_request.httprequest = mock_httprequest

        with patch.object(models.res_user, "request", mock_request):
            with self.assertRaises(AccessDenied):
                self.registrant_user._login(
                    db=self.env.cr.dbname,
                    login="registrant_user@example.com",
                    password="AgentUser1!",
                    user_agent_env=None,
                )
