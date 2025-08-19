# pylint: disable=consider-merging-classes-inherited


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    portal_password = fields.Char(store=False)
    portal_password_confirm = fields.Char(store=False)
    show_portal_password = fields.Boolean(compute="_compute_show_portal_password", store=False)

    def _compute_show_portal_password(self):
        show_fields = (
            self.env["ir.config_parameter"].sudo().get_param("g2p_security.show_portal_password", False)
        )
        for record in self:
            record.show_portal_password = bool(show_fields)

    def _check_passwords_match(self, password, confirm):
        if password or confirm:
            if password != confirm:
                raise ValidationError(_("Password and confirm password do not match."))

    @api.model
    def create(self, vals):
        vals.pop("portal_password", None)
        vals.pop("portal_password_confirm", None)

        partner = super().create(vals)

        if partner.supplier_rank == 1:
            if not partner.email:
                raise ValidationError(_("Email is required to create a portal user."))

            user_vals = {
                "name": partner.name,
                "login": partner.email,
                "partner_id": partner.id,
                "groups_id": [(6, 0, [self.env.ref("base.group_portal").id])],
            }
            self.env["res.users"].sudo().create(user_vals)

        return partner

    def write(self, vals):
        password = vals.pop("portal_password", None)
        confirm = vals.pop("portal_password_confirm", None)

        self._check_passwords_match(password, confirm)

        res = super().write(vals)

        for partner in self:
            user = partner.user_ids[:1]
            if user and user.has_group("base.group_portal"):
                if "email" in vals and partner.email:
                    user.sudo().write({"login": partner.email})
                if password:
                    user.sudo().write({"password": password})

        return res
