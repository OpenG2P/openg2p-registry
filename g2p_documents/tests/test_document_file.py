import base64
import io
from unittest.mock import patch

from PIL import Image

from odoo.exceptions import UserError

from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentFile(TransactionComponentCase):
    # Setup test environment by creating a storage backend and a sample file.
    def setUp(self):
        super().setUp()
        self.storage_backend = self.env["storage.backend"].create({"name": "Test Backend"})

        # Sample data and file creation with base64 encoding
        self.test_data = b"Test Data"
        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(self.test_data),
            }
        )

    # Test filtering of files based on tags, including multiple and non-existent tags.
    def test_filter_for_tags_multiple(self):
        tag1 = self.env["g2p.document.tag"].create({"name": "Tag1"})
        tag2 = self.env["g2p.document.tag"].create({"name": "Tag2"})

        # Creating files with different tags
        file1 = self.env["storage.file"].create(
            {
                "name": "test1.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(b"test data 1"),
                "tags_ids": [(6, 0, [tag1.id])],
            }
        )

        file2 = self.env["storage.file"].create(
            {
                "name": "test2.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(b"test data 2"),
                "tags_ids": [(6, 0, [tag2.id])],
            }
        )

        # Test filtering by individual tags
        files = self.env["storage.file"].search([])

        # Filter by Tag1
        filtered = files.filter_for_tags(["Tag1"])
        self.assertEqual(filtered[0].id, file1.id)

        # Filter by Tag2 (any of the tags)
        filtered = files.filter_for_tags_any(["Tag2"])
        self.assertEqual(filtered[0].id, file2.id)

        # Filter by both Tag1 and Tag2 (any matching tags)
        filtered = files.filter_for_tags_any(["Tag1", "Tag2"])
        self.assertEqual(len(filtered), 2)

        # Test with non-existent tag (should return empty result)
        filtered = files.filter_for_tags_any(["NonExistentTag"])
        self.assertEqual(len(filtered), 0)

    # Test filtering for tags with "any" logic.
    def test_filter_for_tags_any(self):
        tag1 = self.env["g2p.document.tag"].create({"name": "Tag1"})
        self.test_file.write({"tags_ids": [(6, 0, [tag1.id])]})

        files = self.env["storage.file"].search([])
        # Filter files with Tag1 or a non-existent tag
        filtered = files.filter_for_tags_any(["Tag1", "NonExistentTag"])
        self.assertEqual(len(filtered), 1)

    # Test automatic file type detection based on file content (e.g., PNG images).
    def test_compute_file_type(self):
        img_data = Image.new("RGB", (60, 30), color="red")
        img_byte_arr = io.BytesIO()
        img_data.save(img_byte_arr, format="PNG")

        image_file = self.env["storage.file"].create(
            {
                "name": "test.png",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(img_byte_arr.getvalue()),
                "mimetype": "image/png",
            }
        )

        # Test file type computation (should be PNG)
        image_file._compute_file_type()
        self.assertEqual(image_file.file_type, "PNG")

    # Test extraction of filename and extension from stored file data.
    def test_compute_extract_filename(self):
        self.test_file._compute_extract_filename()
        # Extract filename (should be 'test') and extension (should be '.txt')
        self.assertEqual(self.test_file.filename, "test")
        self.assertEqual(self.test_file.extension, ".txt")

    # Test MIME type detection from file content.
    def test_compute_mime_type(self):
        img_data = Image.new("RGB", (60, 30), color="red")
        img_byte_arr = io.BytesIO()
        img_data.save(img_byte_arr, format="PNG")

        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(img_byte_arr.getvalue()),
            }
        )

        self.assertTrue(self.test_file.mimetype.startswith("image/png"))

        # Invalid data (should return None)
        self.test_file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(b"invalid data"),
            }
        )
        self.assertFalse(self.test_file.mimetype)

    # Test error handling during file data computation (simulate backend error).
    def test_compute_data_key_error(self):
        file = self.env["storage.file"].create(
            {
                "name": "test.txt",
                "backend_id": self.storage_backend.id,
                "data": base64.b64encode(self.test_data),
            }
        )

        # Simulate an error while retrieving the file from backend
        with patch.object(file.backend_id.__class__, "get", side_effect=Exception("NoSuchKey")):
            # Expect a UserError with a specific message
            with self.assertRaises(UserError) as cm:
                file._compute_data()

            self.assertEqual(str(cm.exception), "The file with the given name is not present on the s3.")
