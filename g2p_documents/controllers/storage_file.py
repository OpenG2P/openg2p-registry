import base64

from werkzeug.exceptions import Forbidden

from odoo.http import request, route

from odoo.addons.storage_file.controllers.main import StorageFileController


class StorageFileControllerExt(StorageFileController):
    @route(["/storage.file/<string:slug_name_with_id>"], type="http", auth="public")
    def content_common(self, slug_name_with_id, **kw):
        # Access control
        storage_file_api_enabled = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_documents.enable_storage_file_api", "user")
        )
        if storage_file_api_enabled == "user":
            if (not request.env.user) or (not request.env.user.has_group("base.group_user")):
                raise Forbidden("You don't have the permission to access the requested resource.")
        elif storage_file_api_enabled == "public":
            pass
        else:
            raise request.not_found()
        file = request.env["storage.file"].sudo().get_from_slug_name_with_id(slug_name_with_id)
        if not file or not file.exists():
            return request.not_found()

        file_data = base64.b64decode(file.data or "")
        mimetype = file.mimetype or "application/octet-stream"

        headers = [("Content-Type", mimetype)]
        return request.make_response(file_data, headers)
