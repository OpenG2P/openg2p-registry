import werkzeug.urls

from odoo import _, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_signup_url_for_action(self, *args, **kwargs):
        res = super()._get_signup_url_for_action(*args, **kwargs)

        Param = self.env["ir.config_parameter"].sudo()
        hide_db_param = Param.get_param("g2p_security.hide_db_param", default="False") == "True"

        if hide_db_param:
            for pid, url in res.items():
                if url and "db=" in url:
                    parsed = werkzeug.urls.url_parse(url)
                    query = parsed.decode_query()
                    query.pop("db", None)
                    cleaned_url = parsed.replace(query=werkzeug.urls.url_encode(query)).to_url()
                    res[pid] = cleaned_url
        return res

    def action_change_password(self):
        """Open change password wizard for partner's user account"""
        if not self.user_ids:
            raise UserError(_("No user account found for this partner"))

        user = self.user_ids[0]

        wizard = self.env["change.password.wizard"].create(
            {
                "user_ids": [
                    (
                        0,
                        0,
                        {
                            "user_id": user.id,
                            "user_login": user.login,
                            "new_passwd": "",
                        },
                    )
                ]
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Change Password"),
            "res_model": "change.password.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "view_id": self.env.ref("base.change_password_wizard_view").id,
            "target": "new",
            "context": {"default_user_ids": wizard.user_ids.ids},
        }
