from odoo.tests.common import HttpCase


class TestAgentPortalBase(HttpCase):
    def setUp(self):
        super().setUp()
        # Create an agent partner and mark as supplier
        agent_partner = self.env["res.partner"].create(
            {
                "name": "Agent Partner",
                "supplier_rank": 1,
            }
        )
        self.agent_user = self.env["res.users"].create(
            {
                "name": "Agent User",
                "login": "agent_user",
                "email": "agent_user@example.com",
                "partner_id": agent_partner.id,
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.agent_user.write({"password": "AgentUser1!"})

        # Create a regular partner and mark as not a supplier
        regular_partner = self.env["res.partner"].create(
            {
                "name": "Regular Partner",
                "supplier_rank": 0,
            }
        )
        self.regular_user = self.env["res.users"].create(
            {
                "name": "Regular User",
                "login": "regular_user",
                "email": "regular_user@example.com",
                "partner_id": regular_partner.id,
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.regular_user.write({"password": "RegularUser1!"})

    def test_portal_root_redirect_logged_in(self):
        # Test if /portal redirects properly for authenticated user
        self.authenticate("agent_user", "AgentUser1!")

        response = self.url_open("/portal")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.url.endswith("/portal/home"))

    def test_portal_root_redirect_logged_out(self):
        # Test if /portal redirects properly for non-auth user
        response = self.url_open("/portal")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.url.endswith("/portal/login"))

    def test_registration_login_redirect_logged_in(self):
        # Test redirection if user is already logged in
        self.authenticate("agent_user", "AgentUser1!")  # Log in the test user

        # Should redirect to /portal/home
        response = self.url_open("/portal/login")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.url.endswith("/portal/home"))

    def test_registration_login_page_loads(self):
        # Test that the login page renders correctly
        response = self.url_open("/portal/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"login", response.content.lower())

    def test_portal_home_access_logged_in(self):
        # Test /portal/home for agents
        self.authenticate("agent_user", "AgentUser1!")

        response = self.url_open("/portal/home")
        self.assertEqual(response.status_code, 200)

    def test_portal_profile(self):
        # Test /portal/myprofile for logged-in users
        self.authenticate("agent_user", "AgentUser1!")

        response = self.url_open("/portal/myprofile")

        self.assertEqual(response.status_code, 200)

    def test_portal_about_us(self):
        # Test /portal/aboutus is publicly accessible
        response = self.url_open("/portal/aboutus")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"About Us", response.content)

    def test_portal_contact_us(self):
        # Test /portal/contactus is publicly accessible
        response = self.url_open("/portal/contactus")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Contact Us", response.content)

    def test_portal_other_page(self):
        # Test /portal/otherpage is publicly accessible
        response = self.url_open("/portal/otherpage")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"otherpage", response.content)
