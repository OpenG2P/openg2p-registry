from odoo import _, models


class Registrant(models.Model):
    _inherit = "res.partner"

    def view_deduplicator_duplicates(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "g2p_registry_deduplication_deduplicator.view_duplicates_client_action",
            "target": "new",
            "name": _("Duplicates"),
            "params": {
                "record_id": self.id,
            },
            "context": {},
        }
