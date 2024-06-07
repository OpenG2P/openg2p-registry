import base64
import io

from PIL import Image

from odoo import models
from odoo.exceptions import ValidationError


class G2PImageStorage(models.Model):
    _inherit = "res.partner"

    def write(self, values):
        profile_tag = self.env["g2p.document.tag"].get_tag_by_name("Profile Image")
        if not profile_tag:
            profile_tag = self.env["g2p.document.tag"].create({"name": "Profile Image"})
        storage_file = self.env["storage.file"].search(
            [("registrant_id", "=", self.id), ("tags_ids", "in", [profile_tag.id])], limit=1
        )

        backend_id = self.env["storage.backend"].search([("name", "=", "Default S3 Document Store")], limit=1)

        if values and values.get("image_1920") is not False:
            img = values.get("image_1920", False)
            if img:
                binary_image = base64.b64decode(img)
                image_size = len(binary_image)

                if image_size > 1 * 1024 * 1024:  # Image is > 1 MB
                    try:
                        # Scale down the image to be less than 1 MB
                        scaled_down_image = self._resize_image(binary_image)
                        values["image_1920"] = scaled_down_image

                    except Exception as e:
                        raise ValidationError(f"Error: {e}") from e

                    storage_file_vals = {
                        "data": img,
                        "file_size": image_size,
                        "name": "Profile Image",
                        "tags_ids": [(4, profile_tag.id)],
                        "registrant_id": self.id,
                        "backend_id": backend_id.id,
                    }

                    if storage_file:
                        storage_file.unlink()
                    self.env["storage.file"].create(storage_file_vals)
                else:
                    if storage_file:
                        storage_file.unlink()
                    values["image_1920"] = img

        else:
            if values and storage_file:
                storage_file.unlink()

        result = super().write(values)
        return result

    def _resize_image(self, binary_image):
        image_stream = io.BytesIO(binary_image)
        image = Image.open(image_stream)
        image_format = image.format
        max_size = 1 * 1024 * 1024  # 1 MB

        # resizing with thumbnail
        image.thumbnail((1024, 1024), Image.ANTIALIAS)

        buffered = io.BytesIO()
        image.save(buffered, format=image_format, optimize=True, quality=85)

        # size of the buffered image
        if buffered.tell() <= max_size:
            return base64.b64encode(buffered.getvalue())

        for quality in range(80, 20, -10):
            buffered = io.BytesIO()
            image.save(buffered, format=image_format, optimize=True, quality=quality)
            if buffered.tell() <= max_size:
                return base64.b64encode(buffered.getvalue())

        # If quality reduction is not enough, reduce dimensions further
        new_width = image.size[0]
        new_height = image.size[1]
        while buffered.tell() > max_size and (new_width > 100 and new_height > 100):
            new_width = int(new_width * 0.9)
            new_height = int(new_height * 0.9)
            image = image.resize((new_width, new_height), Image.ANTIALIAS)
            buffered = io.BytesIO()
            image.save(buffered, format=image_format, optimize=True, quality=85)
            if buffered.tell() <= max_size:
                break

        return base64.b64encode(buffered.getvalue())
