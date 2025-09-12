from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_portal_password = fields.Boolean(
        string="Enable Portal Password Fields",
        config_parameter="g2p_security.show_portal_password",
        default=False,
    )
