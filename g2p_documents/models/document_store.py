import base64
import uuid

from odoo import _, models


class G2PDocumentStore(models.Model):
    _inherit = "storage.backend"

    def open_store_files_tree(self):
        return {
            "name": _("Document Store Files"),
            "type": "ir.actions.act_window",
            "res_model": "storage.file",
            "view_mode": "tree,form",
            "views": [
                (self.env.ref("g2p_documents.view_g2p_document_files_tree").id, "tree"),
                (self.env.ref("storage_file.storage_file_view_form").id, "form"),
            ],
            "search_view_id": self.env.ref("storage_file.storage_file_view_search").id,
            "context": {"hide_backend": 1},
            "domain": [("backend_id", "=", self.id)],
        }

    def add_file(self, data, name=None, extension=None, tags=None):
        if not name:
            name = self._gen_random_name()
        if extension:
            name += extension
        tags_ids = []
        if tags:
            if not (isinstance(tags, list) or isinstance(tags, tuple)):
                tags = [
                    tags,
                ]
            for tag in tags:
                if isinstance(tag, str):
                    tag_id = self.env["g2p.document.tag"].get_tag_by_name(tag)
                    if tag_id:
                        tags_ids.append((4, tag_id.id))
                    else:
                        tags_ids.append((0, 0, {"name": tag}))
                else:
                    tags_ids.append(tag)
        return self.env["storage.file"].create(
            {
                "name": name,
                "backend_id": self.id,
                "data": base64.b64encode(data),
                "tags_ids": tags_ids,
            }
        )

    def _gen_random_name(self, length=10):
        return str(uuid.uuid4())
