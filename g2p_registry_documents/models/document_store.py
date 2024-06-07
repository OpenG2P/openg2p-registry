from odoo import models


class G2PDocumentStore(models.Model):
    _inherit = "storage.backend"

    def add_file_registrant(self, data, name=None, extension=None, registrant=None, **kwargs):
        res = super().add_file(data, name=name, extension=extension, **kwargs)
        if registrant:
            res.registrant_id = registrant
        return res
