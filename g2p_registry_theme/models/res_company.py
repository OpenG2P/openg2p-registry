import base64

from odoo import models, tools
from odoo.modules.module import get_resource_path


class ResCompany(models.Model):
    _inherit = "res.company"

    def get_g2p_favicon(self, img_path_module="", img_path_rel=""):
        img_path = get_resource_path(
            img_path_module if img_path_module else "g2p_registry_theme",
            img_path_rel if img_path_rel else "static/src/img/favicon-white-background.png",
        )
        with tools.file_open(img_path, "rb") as f:
            return base64.b64encode(f.read())
