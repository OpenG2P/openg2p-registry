from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class G2PGender(models.Model):
    _name = "gender.type"
    _rec_name = "code"

    code = fields.Char()
    value = fields.Char()
    active = fields.Boolean(default=True)

    @api.constrains("code")
    def _check_name(self):
        group_types = self.search([])
        for record in self:
            if not record.code:
                error_message = _("Gender type should not empty.")
                raise ValidationError(error_message)
        for record in group_types:
            if self.code.lower() == record.code.lower() and self.id != record.id:
                raise ValidationError(_("Gender type should be unique"))
