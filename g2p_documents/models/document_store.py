from odoo import _, fields, models


class G2PDocumentStore(models.Model):
    _inherit = "storage.backend"

    mimetype_strategy = fields.Selection(
        selection=[("from_data", "Guess from Data"), ("from_file_name", "Guess from filename")],
        default="from_data",
        help="Mimetype of a file can be inferred from the filename or from the binary data.",
    )

    virus_scan_url = fields.Char(string="Virus Scan URL")

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update({"mimetype_strategy": {}, "virus_scan_url": {}})
        return env_fields

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
