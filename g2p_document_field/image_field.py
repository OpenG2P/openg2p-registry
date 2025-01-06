import base64

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tools import image_process

from .binary_field import DocumentBinaryField


class DocumentImageField(DocumentBinaryField, fields.Image):
    """Encapsulates an DocumentBinaryField, extending :class:`DocumentBinaryField`.

    The rest of the properties are similar to :class:`odoo.fields.Image`.

    Donot use this field for computed or related fields.
    Use :class:`odoo.fields.Image` instead.

    :param str documents_field: the One2many field containing linked documents.
    :param function get_tags_func: Func to call to get Document tag(s).
    :param function get_storage_backend_func: Func to call to get storage backend.
    :param int max_width: the maximum width of the image (default: ``0``, no limit)
    :param int max_height: the maximum height of the image (default: ``0``, no limit)
    :param bool verify_resolution: whether the image resolution should be verified
        to ensure it doesn't go over the maximum image resolution (default: ``True``).
        See :class:`odoo.tools.image.ImageProcess` for maximum image resolution (default: ``50e6``).
    """

    def _image_process(self, value, env):
        if not self.max_width and not self.max_height:
            # no need to process images where neither max_height nor max_width is set
            return value
        try:
            img = base64.b64decode(value or "") or False
        except Exception as e:
            raise UserError(_("Image is not encoded in base64.")) from e

        # Removing the webp check present in `odoo.fields.Image`.
        # TBD alternative.

        return (
            base64.b64encode(
                image_process(
                    img,
                    size=(self.max_width, self.max_height),
                    verify_resolution=self.verify_resolution,
                )
                or b""
            )
            or False
        )
