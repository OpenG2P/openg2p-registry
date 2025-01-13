import base64
from unittest.mock import patch

from odoo.tests.common import HttpCase


class TestCustomStorageFileController(HttpCase):
    def setUp(self):
        super().setUp()
        # Create a sample storage file for tests
        self.env["g2p.document.tag"].create({"name": "Profile Image"})
        backend = self.env["storage.backend"].create({"name": "Test Backend"})
        self.storage_file = self.env["storage.file"].create(
            {
                "name": "test_file.txt",
                "mimetype": "text/plain",
                "data": base64.b64encode(b"Sample Data"),
                "is_encrypted": False,
                "backend_id": backend.id,
            }
        )
        self.slug_name_with_id = f"{self.storage_file.name.replace(' ', '_')}-{self.storage_file.id}"

    @patch("odoo.addons.storage_file.models.storage_file.StorageFile.get_from_slug_name_with_id")
    @patch("odoo.addons.base.models.ir_config_parameter.IrConfigParameter.get_param", return_value=False)
    def test_content_common_without_encryption(self, mock_get_param, mock_get_from_slug_name_with_id):
        """Test the controller without encryption enabled."""
        mock_get_from_slug_name_with_id.return_value = self.storage_file
        response = self.url_open(f"/storage.file/{self.slug_name_with_id}")
        self.assertEqual(response.status_code, 200)

    @patch("odoo.addons.storage_file.models.storage_file.StorageFile.get_from_slug_name_with_id")
    @patch("odoo.addons.base.models.ir_config_parameter.IrConfigParameter.get_param", return_value=False)
    def test_content_common_with_encryption_disabled(self, mock_get_param, mock_get_from_slug_name_with_id):
        """Test the controller with encryption disabled."""
        mock_get_from_slug_name_with_id.return_value = self.storage_file
        response = self.url_open(f"/storage.file/{self.slug_name_with_id}")
        self.assertEqual(response.status_code, 200)

    @patch("odoo.addons.g2p_encryption.models.encryption_provider.G2PEncryptionProvider.decrypt_data")
    @patch("odoo.addons.base.models.ir_config_parameter.IrConfigParameter.get_param", return_value=True)
    @patch("odoo.addons.storage_file.models.storage_file.StorageFile.get_from_slug_name_with_id")
    def test_content_common_with_encryption_enabled(
        self, mock_get_from_slug_name_with_id, mock_get_param, mock_decrypt_data
    ):
        """Test the controller with encryption enabled."""
        self.storage_file.is_encrypted = True
        mock_get_from_slug_name_with_id.return_value = self.storage_file
        mock_decrypt_data.return_value = b"Decrypted Data"

        response = self.url_open(f"/storage.file/{self.slug_name_with_id}")
        mock_decrypt_data.assert_called_once_with(base64.b64decode(self.storage_file.data))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Decrypted Data")
        self.assertIn("text/plain", response.headers.get("Content-Type"))
