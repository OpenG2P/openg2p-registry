import logging

from odoo import api, fields, models
from odoo.http import request

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


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        result = super()._authenticate(endpoint=endpoint)
        if (
            request
            and request.session
            and request.session.uid
            and not request.env["res.users"].browse(request.session.uid)._is_public()
        ):
            if request.httprequest.path:
                last_activity = request.session.get("last_activity")
                current_time = fields.Datetime.now()
                if last_activity and last_activity < current_time:
                    request.env.user._handle_session_timeout(last_activity, current_time)
                else:
                    request.session["last_activity"] = current_time

        return result


class ResUsers(models.Model):
    _inherit = "res.users"

    def _is_session_expired(self, last_activity, current_time, timeout_duration):
        elapsed_seconds = (current_time - last_activity).total_seconds()
        return elapsed_seconds > timeout_duration

    def _logout_user_session(self):
        if request.session.db and request.session.uid:
            request.session.logout(keep_db=True)
        return True

    def _handle_session_timeout(self, last_activity, current_time):
        session_config = self.env["ir.config_parameter"].sudo()._get_session_config()
        is_timeout_active = session_config.get("inactive_session_timeout_active", False)

        if not is_timeout_active:
            request.session["last_activity"] = current_time
            return

        timeout_duration = session_config.get("inactive_session_timeout_seconds", 7200)
        if self._is_session_expired(last_activity, current_time, timeout_duration):
            self._logout_user_session()
        else:
            request.session["last_activity"] = current_time
