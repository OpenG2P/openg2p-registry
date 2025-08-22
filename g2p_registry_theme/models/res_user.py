import logging

from odoo import SUPERUSER_ID, _, api, models
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    _inherit = "res.users"

    def reset_password(self, login):
        """retrieve the user corresponding to login (login or email),
        and reset their password
        """
        users = self.search([("login", "=", login)])
        if not users:
            users = self.search([("email", "=", login)])
        if len(users) != 1:
            raise Exception(_("Incorrect email. Please enter the registered email address."))
        return users.action_reset_password()

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        # Self-service provider access denied into openg2p
        user_id = super()._login(db, login, password, user_agent_env)
        if request and request.httprequest.path.startswith("/web/login"):
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                user = self.sudo().search([("login", "=", login)])
                if user and user.partner_id.is_registrant:
                    raise AccessDenied()

        return user_id
