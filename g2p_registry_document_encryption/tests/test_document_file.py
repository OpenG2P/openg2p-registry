import base64
from unittest.mock import patch

from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentRegistry(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        # Set up a sample storage backend and a file
        self.storage_backend = self.env["storage.backend"].create({"name": "Test Backend"})
        self.registrant = self.env["res.partner"].create({"name": "Test Registrant"})
        self.test_data = b"Test Data"
        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(self.test_data),
                "registrant_id": self.registrant.id,
            }
        )

    @patch("odoo.addons.g2p_documents.models.document_file.G2PDocumentFile._get_mime_type")
    @patch("requests.post")
    @patch("odoo.addons.base.models.ir_config_parameter.IrConfigParameter.get_param")
    @patch("odoo.addons.g2p_registry_document_encryption.models.document_store.G2PDocumentStore.add")
    @patch("odoo.addons.g2p_encryption.models.encryption_provider.G2PEncryptionProvider.encrypt_data")
    def test_inverse_data_encryption_enabled(
        self,
        mock_encrypt_data,
        mock_get_param,
        mock_requests_post,
        mock_get_mime_type,
        mock_add,
    ):
        # Mock MIME type detection to return 'text/plain'
        mock_get_mime_type.return_value = "text/plain"

        # Mock the 'get_param' method to return True for 'encrypt_registry'
        mock_get_param.return_value = True

        # Provide a mock JWT access token
        mock_jwt_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ik1vY2sgVXNlciIsImlhdCI6MTUxNjIzOTAyMn0."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )

        # Mock the HTTP request to return the mock access token
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = {
            "access_token": mock_jwt_token,
            "expires_in": 3600,
        }

        # Mock the behavior of the encrypt_data method
        mock_encrypt_data.return_value = b"Encrypted Data"

        # Call the method
        self.test_file._inverse_data()

        # Verify that the file is marked as encrypted
        self.assertTrue(self.test_file.is_encrypted)

    def test_inverse_data_encryption_disabled(self):
        # Ensure encryption is disabled
        self.env["ir.config_parameter"].sudo().set_param("g2p_registry_encryption.encrypt_registry", False)

        # Call the method
        self.test_file._inverse_data()

        # Verify the file is not marked as encrypted
        self.assertFalse(self.test_file.is_encrypted)

    @patch("odoo.addons.g2p_documents.models.document_file.G2PDocumentFile._get_mime_type")
    def test_inverse_data_with_missing_mimetype(self, mock_get_mime_type):
        # Mock MIME type detection to return 'text/plain'
        mock_get_mime_type.return_value = "text/plain"

        # Create a new file with no mimetype set
        test_data = base64.b64encode(b"Sample Data")
        test_file = self.env["storage.file"].create(
            {
                "name": "new_test",
                "backend_id": self.storage_backend.id,
                "data": test_data,
                "registrant_id": self.registrant.id,
                "mimetype": None,  # Ensure mimetype is not set
            }
        )

        # Call the inverse method
        test_file._inverse_data()

        # Assert that MIME type was determined and set
        self.assertEqual(test_file.mimetype, "text/plain")
        # mock_get_mime_type.assert_called_once_with(base64.b64decode(test_data))
