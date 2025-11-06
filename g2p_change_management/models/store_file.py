import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ChangeRequestSupportingDocument(models.Model):
    _inherit = "storage.file"

    change_request_id = fields.Many2one(
        "g2p.change.request",
        string="Change Request",
        index=True,
        help="The change request this document is associated with.",
    )
