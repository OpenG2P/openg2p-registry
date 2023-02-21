import json

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    additional_g2p_info = fields.Text("Additional Information", default="{}")

    @api.onchange("additional_g2p_info")
    def _onchange_additional_g2p_info(self):
        for rec in self:
            if rec.additional_g2p_info:
                addl_json = {}
                try:
                    addl_json = json.loads(rec.additional_g2p_info)
                except ValueError as ve:
                    raise ValidationError(
                        _("Additional Information is not valid json.")
                    ) from ve
                rec.additional_g2p_info = json.dumps(addl_json, separators=(",", ":"))
