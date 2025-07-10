# pylint: disable=consider-merging-classes-inherited


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    portal_password = fields.Char()
    portal_password_confirm = fields.Char()
    show_portal_password = fields.Boolean(compute="_compute_show_portal_password", store=False, default=False)

    def _compute_show_portal_password(self):
        show_fields = (
            self.env["ir.config_parameter"].sudo().get_param("g2p_security.show_portal_password", False)
        )
        for record in self:
            record.show_portal_password = bool(show_fields)

    @api.constrains("portal_password", "portal_password_confirm")
    def _check_password_match(self):
        for partner in self:
            if partner.portal_password or partner.portal_password_confirm:
                if partner.portal_password != partner.portal_password_confirm:
                    raise ValidationError(_("Password and confirm password do not match."))

    def write(self, vals):
        res = super().write(vals)
        if "portal_password" in vals:
            for partner in self:
                user = partner.user_ids[:1]
                if user and user.has_group("base.group_portal"):
                    user.sudo().write({"password": vals["portal_password"]})
        return res
