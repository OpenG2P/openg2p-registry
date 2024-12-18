from odoo import fields, models


class RegistryConfig(models.TransientModel):
    _inherit = "res.config.settings"

    enable_odk = fields.Boolean(config_parameter="g2p_odk_importer.enable_odk")
    enable_odk_async = fields.Boolean(config_parameter="g2p_odk_importer.enable_odk_async")
