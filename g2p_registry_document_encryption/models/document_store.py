import base64

from odoo import models


class G2PDocumentStore(models.Model):
    _inherit = "storage.backend"

    def add(self, relative_path, data, binary=True, registrant_id=None, **kwargs):
        if not binary:
            data = base64.b64decode(data)

        is_encrypt_fields = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry_encryption.encrypt_registry", default=False)
        )

        if is_encrypt_fields and registrant_id:
            prov = self.env["g2p.encryption.provider"].get_registry_provider()
            data = prov.encrypt_data(data)

        return self._forward("add", relative_path, data, **kwargs)
