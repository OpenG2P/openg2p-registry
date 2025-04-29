# pylint: disable=consider-merging-classes-inherited

from odoo import models
from odoo.http import request


def is_user_debug_restricted(user=None):
    """Utility function to check if the user is restricted from using Debug Mode."""
    if not user:
        user_id = request.session.uid
        user = request.env["res.users"].sudo().browse(user_id)
    return user.has_group("g2p_security.group_restrict_debug_mode")


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _handle_debug(cls):
        if is_user_debug_restricted(request.env.user):
            request.session.debug = ""
        else:
            return super()._handle_debug()
