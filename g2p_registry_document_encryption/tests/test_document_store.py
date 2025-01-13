import base64
from unittest.mock import patch

from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentStore(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        # Set up a sample storage backend
        self.storage_backend = self.env["storage.backend"].create({"name": "Test Backend"})
        self.registrant = self.env["res.partner"].create({"name": "Test Registrant"})
        self.test_data = b"Test Data"
        self.relative_path = "test/path/test.txt"

    @patch("odoo.addons.g2p_encryption.models.encryption_provider.G2PEncryptionProvider.encrypt_data")
    @patch("odoo.addons.base.models.ir_config_parameter.IrConfigParameter.get_param")
    @patch("odoo.addons.storage_backend.models.storage_backend.StorageBackend._forward")
    def test_add_with_encryption(self, mock_forward, mock_get_param, mock_encrypt_data):
        # Mock the 'get_param' method to simulate encryption being enabled
        mock_get_param.return_value = True

        # Mock the 'encrypt_data' method to return encrypted data
        encrypted_data = b"Encrypted Data"
        mock_encrypt_data.return_value = encrypted_data

        # Mock the '_forward' method to simulate file addition
        mock_forward.return_value = True

        # Call the 'add' method
        result = self.storage_backend.add(
            self.relative_path,
            base64.b64encode(self.test_data),  # Input as base64-encoded data
            binary=False,
            registrant_id=self.registrant.id,
        )

        # Verify the encrypt_data method was called with the correct arguments
        mock_encrypt_data.assert_called_once_with(self.test_data)

        # Verify the _forward method was called with the encrypted data
        mock_forward.assert_called_once_with("add", self.relative_path, encrypted_data)

        # Verify the result
        self.assertTrue(result)
