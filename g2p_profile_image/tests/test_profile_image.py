import base64
import io

from PIL import Image

from odoo.tests import tagged

from odoo.addons.component.tests.common import TransactionComponentCase


@tagged("post_install", "-at_install")
class TestProfileImage(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.profile_tag = self.env["g2p.document.tag"].search([("name", "=", "Profile Image")], limit=1)
        if not self.profile_tag:
            self.profile_tag = self.env["g2p.document.tag"].create({"name": "Profile Image"})
        self.backend = self.env["storage.backend"].search(
            [("name", "=", "Default S3 Document Store")], limit=1
        )
        if not self.backend:
            self.backend = self.env["storage.backend"].create({"name": "Default S3 Document Store"})

    def create_image(self, size):
        img = Image.new("RGB", (size, size), color="red")
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def test_upload_image_less_than_1mb(self):
        img_str = self.create_image(100)  # Creates a small image
        self.partner.write({"image_1920": img_str})

        # decoding stored and original image strings to compare binary data
        stored_image = base64.b64decode(self.partner.image_1920)
        original_image = base64.b64decode(img_str)

        self.assertEqual(stored_image, original_image, "Image should be stored correctly in the database")
        storage_files = self.env["storage.file"].search([("registrant_id", "=", self.partner.id)])
        self.assertFalse(storage_files, "No file should be stored in the S3 bucket for image <= 1MB")

    def test_upload_image_more_than_1mb(self):
        img_str = self.create_image(10000)
        self.partner.write({"image_1920": img_str})

        # to check if the image is resized and stored in the database
        resized_img_str = self.partner.image_1920
        self.assertNotEqual(resized_img_str, img_str, "Image should be resized")
        self.assertLess(
            len(base64.b64decode(resized_img_str)), 1 * 1024 * 1024, "Resized image should be less than 1MB"
        )

        # Checking if the original image is stored in the S3 bucket
        storage_file = self.env["storage.file"].search([("registrant_id", "=", self.partner.id)], limit=1)
        self.assertTrue(storage_file, "Original image should be stored in the S3 bucket")
        self.assertEqual(
            storage_file.name, "Profile Image", "Stored file should have the tag 'Profile Image'"
        )
        self.assertEqual(
            storage_file.file_size,
            len(base64.b64decode(img_str)),
            "File size should match the original image size",
        )

    def test_delete_image(self):
        img_str = self.create_image(100)
        self.partner.write({"image_1920": img_str})
        self.partner.write({"image_1920": False})

        # Checking if the image is deleted from the database
        self.assertFalse(self.partner.image_1920, "Image should be deleted from the database")

    def test_delete_s3_file_on_image_delete(self):
        img_str = self.create_image(10000)
        self.partner.write({"image_1920": img_str})

        storage_file = self.env["storage.file"].search([("registrant_id", "=", self.partner.id)], limit=1)
        self.assertTrue(storage_file, "Original image should be stored in the S3 bucket")

        # Delete the profile image
        self.partner.write({"image_1920": False})

        # Check that the corresponding entry in the S3 bucket is also deleted
        storage_files = self.env["storage.file"].search([("registrant_id", "=", self.partner.id)])
        self.assertFalse(
            storage_files, "Corresponding S3 entry should be deleted when profile image is removed"
        )
