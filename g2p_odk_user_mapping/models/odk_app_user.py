from odoo import fields, models


class ODKAppUser(models.Model):
    _name = "odk.app.user"
    _description = "ODK App User"

    name = fields.Char(string="ODK App User Name")
    odk_user_id = fields.Integer(string="ODK App User ID")
    partner_id = fields.Many2one("res.partner", string="Partner")
