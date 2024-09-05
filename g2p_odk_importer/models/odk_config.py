import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class OdkConfig(models.Model):
    _name = "odk.config"
    _description = "ODK Configuration"

    name = fields.Char(required=True)
    base_url = fields.Char(string="Base URL", required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    project = fields.Char(required=False)
    form_id = fields.Char(string="Form ID", required=False)
