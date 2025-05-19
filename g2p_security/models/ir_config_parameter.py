import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

SESSION_TIMEOUT_DELAY = "inactive_session_timeout_seconds"
SESSION_TIMEOUT_ACTIVE = "inactive_session_timeout_active"


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    def write(self, values):
        result = super().write(values)
        if SESSION_TIMEOUT_DELAY in values or SESSION_TIMEOUT_ACTIVE in values:
            self.env.registry.clear_cache()
            _logger.info("Session config cache cleared due to session timeout setting update.")
        return result

    @api.model
    def _get_session_config(self):
        config = self.sudo()
        timeout = int(config.get_param(SESSION_TIMEOUT_DELAY, default="7200"))
        active = config.get_param(SESSION_TIMEOUT_ACTIVE, default="False") == "True"
        return {
            SESSION_TIMEOUT_DELAY: timeout,
            SESSION_TIMEOUT_ACTIVE: active,
        }
