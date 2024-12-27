import base64

from odoo import http
from odoo.http import request

from odoo.addons.storage_file.controllers.main import StorageFileController


class CustomStorageFileController(StorageFileController):
    @http.route(["/storage.file/<string:slug_name_with_id>"], type="http", auth="public")
    def content_common(self, slug_name_with_id, token=None, download=None, **kw):
        storage_file = request.env["storage.file"].get_from_slug_name_with_id(slug_name_with_id)
        is_decrypt_fields = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry_encryption.decrypt_registry", default=False)
        )

        if not is_decrypt_fields or not storage_file.is_encrypted:
            return request.env["ir.binary"]._get_image_stream_from(storage_file, "data").get_response()

        prov = request.env["g2p.encryption.provider"].get_registry_provider()
        decrypted_data = prov.decrypt_data(base64.b64decode(storage_file.data))
        return request.make_response(
            decrypted_data,
            headers=[
                ("Content-Type", storage_file.mimetype),
                ("Content-Disposition", f"inline; filename={storage_file.name}"),
                ("Cache-Control", "no-cache"),
            ],
        )
