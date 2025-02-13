from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestWellKnownRouter(TransactionCase):
    @patch("odoo.addons.g2p_encryption_rest_api.routers.well_known.odoo_env")
    def test_get_jwks_success(self, mock_odoo_env):
        mock_env = MagicMock()
        mock_odoo_env.return_value = mock_env

        mock_provider1 = MagicMock()
        mock_provider1.get_jwks.return_value = {"keys": [{"kty": "RSA", "kid": "key1"}]}
        mock_provider2 = MagicMock()
        mock_provider2.get_jwks.return_value = {"keys": [{"kty": "RSA", "kid": "key2"}]}

        mock_env["g2p.encryption.provider"].sudo().search.return_value = [mock_provider1, mock_provider2]

        from ..routers.well_known import get_jwks

        result = get_jwks(mock_env)

        self.assertEqual(result, {"keys": [{"kty": "RSA", "kid": "key1"}, {"kty": "RSA", "kid": "key2"}]})

    @patch("odoo.addons.g2p_encryption_rest_api.routers.well_known._logger")
    @patch("odoo.addons.g2p_encryption_rest_api.routers.well_known.odoo_env")
    def test_get_jwks_with_exception(self, mock_odoo_env, mock_logger):
        mock_env = MagicMock()
        mock_odoo_env.return_value = mock_env

        mock_provider = MagicMock()
        mock_provider.get_jwks.side_effect = Exception("Mock exception")

        mock_env["g2p.encryption.provider"].sudo().search.return_value = [mock_provider]

        from ..routers.well_known import get_jwks

        result = get_jwks(mock_env)

        self.assertEqual(result, {"keys": []})
        mock_logger.exception.assert_called_once_with("Unable to get JWKS from list of encryption providers")
