# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    region = fields.Many2one("g2p.region")
    unique_id = fields.Char(string="Unique ID", index=True)

    _sql_constraints = [
        ("unique_id_uniq", "UNIQUE(unique_id)", "unique_id is an unique identifier!"),
    ]

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get("is_registrant"):
            record.generate_unique_id()
        return record

    def generate_unique_id(self):
        for rec in self:
            g2p_que_background_task_model = self.env["g2p.que.background.task"].sudo()
            if not g2p_que_background_task_model.search(
                [("worker_payload", "ilike", f'"registrant_id": {rec.id}')]
            ):
                g2p_que_background_task_model.create(
                    {
                        "worker_type": "id_generation_request_worker",
                        "worker_payload": {"registrant_id": rec.id},
                        "task_status": "PENDING",
                    }
                )
