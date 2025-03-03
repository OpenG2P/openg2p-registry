import base64
import logging
import mimetypes
import os
import re
import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)


class G2PDocumentFile(models.Model):
    _inherit = "storage.file"

    tags_ids = fields.Many2many("g2p.document.tag")

    mimetype = fields.Char("Mime Type", compute="_compute_mime_type", store=True)
    file_type = fields.Char(compute="_compute_file_type", store=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        for key in fields_list:
            if key == "name":
                res[key] = self._gen_random_name()
        return res

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

    @api.depends("name", "data", "backend_id")
    def _compute_mime_type(self):
        for rec in self:
            if rec.backend_id.mimetype_strategy == "from_file_name" and rec.name:
                rec.mimetype, __ = mimetypes.guess_type(rec.name)
            elif rec.data:
                # Defaults of "from_data" mode even if empty.
                rec.mimetype = guess_mimetype(base64.b64decode(rec.data))

    def _compute_extract_filename(self):
        for rec in self:
            if rec.name:
                rec.filename, rec.extension = os.path.splitext(rec.name)
            else:
                rec.filename = rec.extension = False

    @api.depends("mimetype")
    def _compute_file_type(self):
        for file in self:
            if isinstance(file.mimetype, str):
                file.file_type = file.mimetype.split("/")[1].upper()
            else:
                file.file_type = False

    def _compute_data(self):
        try:
            return super()._compute_data()
        except Exception as e:
            if "NoSuchKey" in str(e):
                err_msg = "The file with the given name is not present on the s3."
                _logger.error(err_msg)
                raise UserError(_(err_msg)) from e
            else:
                raise

    def _gen_random_name(self):
        return str(uuid.uuid4())

    def get_from_slug_name_with_id(self, slug_name_with_id):
        """
        Return a browse record from a slug generated
        :param slug_name_with_id:
        :return: a BrowseRecord (could be empty...)
        """
        # id is the last group of digit after '-'
        _id = re.findall(r"-([0-9]+)", slug_name_with_id)[-1:]
        if _id:
            _id = int(_id[0])
        res = self.browse(_id)
        if res and slug_name_with_id.startswith(res.filename):
            return res
        # Return empty recordset if slug doesnt match
        return self
