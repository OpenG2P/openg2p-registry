from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestSecurityFastApiEndpoint(TransactionCase):
    def setUp(self):
        super().setUp()
        self.endpoint_model = self.env["fastapi.endpoint"]
        self.security_endpoint = self.endpoint_model.create(
            {"app": "security", "name": "Test Security Endpoint", "root_path": "/test/security"}
        )

    def test_app_field_extension(self):
        self.assertIn(
            ("security", "Security Endpoint"),
            self.endpoint_model._fields["app"].selection,
            "The app field does not include 'Security Endpoint'.",
        )

    @patch("odoo.addons.g2p_encryption_rest_api.routers.well_known.well_known_router", new_callable=MagicMock)
    def test_get_fastapi_routers(self, mock_router):
        self.security_endpoint.app = "security"
        routers = self.security_endpoint._get_fastapi_routers()
        self.assertIn(mock_router, routers, "well_known_router is not included in the routers list.")

    @patch("odoo.models.BaseModel.browse")
    def test_sync_endpoint_id_with_registry(self, mock_browse):
        mock_record = MagicMock()
        mock_browse.return_value = mock_record

        endpoint_id = self.security_endpoint.id
        self.security_endpoint.sync_endpoint_id_with_registry(endpoint_id)

        mock_record.action_sync_registry.assert_called_once_with()
