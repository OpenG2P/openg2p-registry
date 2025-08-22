# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2PGroupKindDeduplication(models.TransientModel):
    _name = "g2p.group.kind.deduplication.config"
    _description = "Deduplication Mapping between Group Kind and ID Types"

    kind_id = fields.Many2one("g2p.group.kind", string="Kind")
    id_type_ids = fields.Many2many("g2p.id.type", string="ID Types")

    _sql_constraints = [
        (
            "unique_group_kind",
            "UNIQUE(kind_id)",
            "The Kind must be unique.",
        ),
    ]
