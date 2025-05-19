from odoo import fields, models
from odoo.http import request


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_session_config(self):
        config_param = self.env["ir.config_parameter"].sudo()
        return config_param._get_session_config()

    def _is_session_expired(self, last_activity, current_time, timeout):
        elapsed_seconds = (current_time - last_activity).total_seconds()
        return elapsed_seconds > timeout

    def _logout_user_session(self):
        if request.session.db and request.session.uid:
            request.session.logout(keep_db=True)
        return True

    def _handle_session_timeout(self, last_activity):
        current_time = fields.Datetime.now()
        session_config = self._get_session_config()

        is_timeout_active = session_config.get("inactive_session_timeout_active", False)
        if not is_timeout_active:
            request.session["last_activity"] = current_time
            return

        if last_activity and last_activity < current_time:
            timeout_delay = session_config.get("inactive_session_timeout_seconds", 7200)
            if self._is_session_expired(last_activity, current_time, timeout_delay):
                self._logout_user_session()
        else:
            request.session["last_activity"] = current_time
