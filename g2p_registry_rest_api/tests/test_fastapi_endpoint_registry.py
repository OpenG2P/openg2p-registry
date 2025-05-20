from unittest.mock import MagicMock, patch

from fastapi import APIRouter, FastAPI

from odoo.tests import TransactionCase, tagged

from ..models.fastapi_endpoint_registry import (
    authenticated_partner_from_basic_auth_user,
    authenticated_partner_impl,
)


@tagged("post_install", "-at_install")
class TestG2PRegistryEndpoint(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create an instance of the endpoint class to test
        self.endpoint = self.env["fastapi.endpoint"].create(
            {"name": "Test Endpoint", "app": "registry", "root_path": "/api/v1/registry"}
        )

    @patch("odoo.addons.g2p_registry_rest_api.models.fastapi_endpoint_registry.FastAPI")
    def test_get_app(self, mock_fastapi):
        # Test _get_app method
        mock_app = MagicMock(spec=FastAPI)
        mock_fastapi.return_value = mock_app

        app = self.endpoint._get_app()

        self.assertIn(authenticated_partner_impl, app.dependency_overrides)
        self.assertEqual(
            app.dependency_overrides[authenticated_partner_impl], authenticated_partner_from_basic_auth_user
        )

    def test_get_fastapi_routers(self):
        # Test _get_fastapi_routers method
        mock_group_router = MagicMock(spec=APIRouter)
        mock_individual_router = MagicMock(spec=APIRouter)

        with patch(
            "odoo.addons.g2p_registry_rest_api.models.fastapi_endpoint_registry.APIRouter"
        ) as mock_apirouter:
            mock_apirouter.side_effect = [mock_group_router, mock_individual_router]

            with patch(
                "odoo.addons.g2p_registry_rest_api.routers.group.group_router", mock_group_router
            ), patch(
                "odoo.addons.g2p_registry_rest_api.routers.individual.individual_router",
                mock_individual_router,
            ):
                routers = self.endpoint._get_fastapi_routers()

        self.assertEqual(len(routers), 2)
        self.assertIn(mock_group_router, routers)
        self.assertIn(mock_individual_router, routers)

    def test_sync_endpoint_id_with_registry(self):
        # Test sync_endpoint_id_with_registry method
        with patch.object(type(self.endpoint), "action_sync_registry", return_value=True) as mock_action_sync:
            result = self.endpoint.sync_endpoint_id_with_registry(self.endpoint.id)

        mock_action_sync.assert_called_once()
        self.assertTrue(result)
