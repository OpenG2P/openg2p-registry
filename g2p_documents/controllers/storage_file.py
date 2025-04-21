from odoo.http import request

from odoo.addons.storage_file.controllers.main import StorageFileController


class StorageFileControllerExt(StorageFileController):
    def content_common(self, *args, **kw):
        storage_file = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_documents.enable_storage_file_api", "False")
            == "True"
        )
        if not storage_file:
            return request.not_found()
        return super().content_common(*args, **kw)
