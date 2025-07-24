from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    g2p_disable_password_login_direct_oauth_provider = fields.Many2one(
        "auth.oauth.provider", config_parameter="g2p_disable_password_login.direct_oauth_provider"
    )
