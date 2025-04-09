from odoo import api, models, tools, http
from odoo.http import request, SessionExpiredException
from os import utime
from os.path import getmtime
from time import time
import logging

_logger = logging.getLogger(__name__)

SESSION_TIMEOUT_KEY = "inactive_session_timeout_seconds"

class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    @tools.ormcache("self.env.cr.dbname")
    def _get_session_timeout(self):
        return int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                SESSION_TIMEOUT_KEY,
                7200,  
            )
        )

    def write(self, values):
        result = super().write(values)
        # Clear the cache to apply session timeout changes across the system
        if SESSION_TIMEOUT_KEY == self.key:
            self.env.registry.clear_cache()
        return result

class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        result = super()._authenticate(endpoint=endpoint)

        # Check if the request has a valid session and user is not public
        if (
            request
            and request.session
            and request.session.uid
            and not request.env["res.users"].browse(request.session.uid)._is_public()
        ):
            request.env.user._check_session_timeout()
        return result

class ResUsers(models.Model):
    _inherit = "res.users"
    
    @api.model
    def _calculate_session_expiry(self):
        config = self.env["ir.config_parameter"]
        timeout_delay = config._get_session_timeout()
        if timeout_delay <= 0:
            return False
        return time() - timeout_delay
    
    @api.model
    def _logout_user_session(self, user_session):
        if user_session.db and user_session.uid:
            user_session.logout(keep_db=True)
        return True

    @api.model
    def _check_session_timeout(self):
        if not http.request:
            return

        user_session = http.request.session
        session_deadline = self._calculate_session_expiry()
        is_session_expired = False
        
        if session_deadline:
            session_file_path = http.root.session_store.get_session_filename(user_session.sid)
            try:
                # Check if the session has expired based on the session file's modification time
                is_session_expired = getmtime(session_file_path) < session_deadline
            except OSError:
                _logger.exception("Error while reading session file's modification time.")
                is_session_expired = True
        
        session_terminated = False
        if is_session_expired:
            session_terminated = self._logout_user_session(user_session)

        if session_terminated:
            return SessionExpiredException("The session has expired.")
        
        # Update the session file's modification time if the user is active
        if http.request.httprequest.path:
            session_file_path = http.root.session_store.get_session_filename(user_session.sid)
            try:
                utime(session_file_path, None)
            except OSError:
                _logger.exception("Error updating session file's access/modified times.")
