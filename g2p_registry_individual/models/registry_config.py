# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class RegistryConfig(models.TransientModel):
    _inherit = "res.config.settings"

    gender_config = fields.Char(store=True)

    def set_values(self):
        res = super(RegistryConfig, self).set_values()
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("g2p_registry.gender_config", self.gender_config)
        return res

    @api.model
    def get_values(self):
        res = super(RegistryConfig, self).get_values()
        res.update(
            gender_config=self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry.gender_config"),
        )
        return res
