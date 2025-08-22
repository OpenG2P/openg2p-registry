import base64

from odoo import tools
from odoo.modules.module import get_resource_path
from odoo.tests import TransactionCase


class TestResCompany(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company_model = self.env["res.company"]

    def test_get_g2p_favicon(self):
        """Test fetching the G2P favicon."""
        company = self.company_model.create(
            {
                "name": "Test Company",
            }
        )
        favicon_base64 = company.get_g2p_favicon()
        expected_img_path = get_resource_path(
            "g2p_registry_theme", "static/src/img/favicon-white-background.png"
        )
        with tools.file_open(expected_img_path, "rb") as f:
            expected_favicon_base64 = base64.b64encode(f.read())
        self.assertEqual(
            favicon_base64, expected_favicon_base64, "The fetched favicon does not match the expected one."
        )
