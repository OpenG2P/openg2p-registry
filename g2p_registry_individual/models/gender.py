from odoo import fields, models


class G2PGender(models.Model):
    _name = "gender.type"
    _rec_name = "code"

    code = fields.Char()
    value = fields.Char()
    active = fields.Boolean(default=True)
