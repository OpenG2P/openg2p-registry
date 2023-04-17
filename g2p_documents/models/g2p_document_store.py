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
        }
