import werkzeug.urls

from odoo import models


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
