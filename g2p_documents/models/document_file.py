import base64
import binascii
import io
import logging
import mimetypes
import os

from PIL import Image

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class G2PDocumentFile(models.Model):
    _inherit = "storage.file"

    tags_ids = fields.Many2many("g2p.document.tag")

    file_type = fields.Char(compute="_compute_file_type")

    def filter_for_tags(self, tags):
        if tags and not isinstance(tags, list):
            tags = [
                tags,
            ]
        return self.filtered(lambda x: all((x.tags_ids and tag in x.tags_ids.name) for tag in tags))

    def filter_for_tags_any(self, tags):
        if tags and not isinstance(tags, list):
            tags = [
                tags,
            ]
        return self.filtered(lambda x: any((x.tags_ids and tag in x.tags_ids.name) for tag in tags))

    def _compute_file_type(self):
        for file in self:
            if file.extension and isinstance(file.mimetype, str):
                file.file_type = file.mimetype.split("/")[1].upper()
            else:
                file.file_type = False

    def _inverse_data(self):
        for record in self:
            record.write(record._prepare_meta_for_file())
            if not record.mimetype:
                binary_data = base64.b64decode(record.data)
                mime = self._get_mime_type(binary_data)
                record.mimetype = mime

            record.backend_id.sudo().add(
                record.relative_path,
                record.data,
                mimetype=record.mimetype,
                binary=False,
            )

    @api.depends("name")
    @api.constrains("name")
    def _compute_extract_filename(self):
        for rec in self:
            if rec.name:
                rec.filename, rec.extension = os.path.splitext(rec.name)
                mime, __ = mimetypes.guess_type(rec.name)
            else:
                rec.filename = rec.extension = mime = False

            if mime is None and rec.data:
                try:
                    binary_data = base64.b64decode(rec.data)
                    mime = self._get_mime_type(binary_data)
                except binascii.Error as e:
                    _logger.info(f"Base64 decoding error: {e}")

            rec.mimetype = mime

    def _get_mime_type(self, binary_data):
        try:
            image = Image.open(io.BytesIO(binary_data))
            mime_type = Image.MIME[image.format]
            return mime_type
        except OSError as e:
            _logger.info(f"Image processing error: {e}")
            return None

    def _compute_data(self):
        # Handled key error
        for rec in self:
            try:
                if self._context.get("bin_size"):
                    rec.data = rec.file_size
                elif rec.relative_path:
                    rec.data = rec.backend_id.sudo().get(rec.relative_path, binary=False)
                else:
                    rec.data = None

            except Exception as e:
                if "NoSuchKey" in str(e):
                    err_msg = "The file with the given name is not present on the s3."
                    _logger.error(err_msg)
                    raise UserError(_(err_msg)) from e
                else:
                    raise
