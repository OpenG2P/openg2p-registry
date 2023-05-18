import base64
import uuid

from odoo import models


class G2PDcoumentStore(models.Model):
    _inherit = "storage.backend"

    def open_store_files_tree(self):
        return {
            "name": "Document Store Files",
            "view_mode": "tree",
            "res_model": "storage.file",
            "view_id": self.env.ref("g2p_documents.view_g2p_document_files_tree").id,
            "type": "ir.actions.act_window",
            "domain": [("backend_id", "=", self.id)],
            "context": {"hide_backend": 1},
        }

    def add_file(self, data, name=None, extension=None):
        if not name:
            name = self._gen_random_name()
        if extension:
            name += extension
        return self.env["storage.file"].create(
            {"name": name, "backend_id": self.id, "data": base64.b64encode(data)}
        )

    def _gen_random_name(self, length=10):
        return str(uuid.uuid4())
