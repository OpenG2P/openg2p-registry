import base64
from unittest.mock import patch

from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentFile(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        # Set up a sample storage backend and a file
        self.storage_backend = self.env["storage.backend"].create({"name": "Test Backend"})

    @patch(
        "odoo.addons.g2p_document_encryption.models.document_store.G2PDocumentStore.get_encryption_provider"
    )
    def test_inverse_data_encryption_enabled(self, mock_get_encryption_provider):
        mock_get_encryption_provider.return_value.encrypt_data.return_value = b"Test Encrypted Data"

        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(b"test_data"),
            }
        )

        # Verify that the file is marked as encrypted
        self.assertTrue(self.test_file.is_encrypted)

    @patch(
        "odoo.addons.g2p_document_encryption.models.document_store.G2PDocumentStore.get_encryption_provider"
    )
    def test_inverse_data_encryption_disabled(self, mock_get_encryption_provider):
        mock_get_encryption_provider.return_value = None

        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(b"test_data"),
            }
        )

        # Verify that the file is marked as encrypted
        self.assertFalse(self.test_file.is_encrypted)

    def test_compute_data_no_relative_path(self):
        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
            }
        )
        self.test_file.relative_path = False
        self.assertFalse(self.test_file.data)

    @patch(
        "odoo.addons.g2p_document_encryption.models.document_store.G2PDocumentStore.get_encryption_provider"
    )
    @patch(
        "odoo.addons.g2p_document_encryption.models.document_store.G2PDocumentStore.get_decryption_provider"
    )
    def test_compute_data_encryption_enabled(
        self, mock_get_decryption_provider, mock_get_encryption_provider
    ):
        mock_get_encryption_provider.return_value.encrypt_data.return_value = b"Test Encrypted Data"
        mock_get_decryption_provider.return_value.decrypt_data.return_value = b"test_data"

        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(b"test_data"),
            }
        )

        # Verify that the file is marked as encrypted
        self.assertTrue(self.test_file.is_encrypted)
        self.assertEqual(base64.b64decode(self.test_file.data), b"test_data")

    @patch(
        "odoo.addons.g2p_document_encryption.models.document_store.G2PDocumentStore.get_encryption_provider"
    )
    @patch(
        "odoo.addons.g2p_document_encryption.models.document_store.G2PDocumentStore.get_decryption_provider"
    )
    def test_compute_data_encryption_disabled(
        self, mock_get_decryption_provider, mock_get_encryption_provider
    ):
        mock_get_encryption_provider.return_value.encrypt_data.return_value = b"Test Encrypted Data"
        mock_get_decryption_provider.return_value = None

        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(b"test_data"),
            }
        )

        # Verify that the file is marked as encrypted
        self.assertTrue(self.test_file.is_encrypted)
        self.assertEqual(base64.b64decode(self.test_file.data), b"Test Encrypted Data")
