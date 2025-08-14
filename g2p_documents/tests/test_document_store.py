import base64
from unittest.mock import patch

from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentStore(TransactionComponentCase):
    # Setup test environment by creating a storage backend.
    def setUp(self):
        super().setUp()
        self.storage_backend = self.env["storage.backend"].create({"name": "Test Backend"})

    # Test the method that opens the file tree for the storage backend.
    def test_open_store_files_tree(self):
        # Call the method to retrieve the store files tree
        result = self.storage_backend.open_store_files_tree()

        # Verify that the returned result matches the expected action window
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "storage.file")
        self.assertEqual(result["view_mode"], "tree,form")
        self.assertEqual(result["context"], {"hide_backend": 1})
        self.assertEqual(result["domain"], [("backend_id", "=", self.storage_backend.id)])

    def test_create_file(self):
        test_data = b"Test data"

        # Add the file with a name and extension
        with patch("uuid.uuid4", return_value="test-uuid"):
            file = self.env["storage.file"].create(
                {
                    "data": base64.b64encode(test_data),
                    "backend_id": self.storage_backend.id,
                }
            )

        # Verify the file name includes the extension and correct data
        self.assertEqual(file.filename, "test-uuid")
        self.assertEqual(file.extension, ".bin")
        self.assertEqual(file.backend_id, self.storage_backend)
        self.assertEqual(file.data, base64.b64encode(test_data))
