from odoo import fields, models
from odoo.http import request


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
                    request.env.user._handle_session_timeout(last_activity)
                else:
                    request.session["last_activity"] = fields.Datetime.now()

        return result

    @classmethod
    def _handle_debug(cls):
        if is_user_debug_restricted(request.env.user):
            request.session.debug = ""
        else:
            return super()._handle_debug()


def is_user_debug_restricted(user=None):
    if not user:
        user_id = request.session.uid
        user = request.env["res.users"].sudo().browse(user_id)
    return user.has_group("g2p_security.group_restrict_debug_mode")
