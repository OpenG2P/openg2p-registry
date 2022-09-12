# Part of OpenSPP. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class RegistryConfig(models.TransientModel):
    _inherit = "res.config.settings"

    # Job Queue fields
    max_registrants_count_job_queue = fields.Integer(
        "Maximum Registrants Before Using Job Queue", default=200
    )
    batch_registrants_count_job_queue = fields.Integer(
        "Number of Registrants Per Batch", default=2000
    )

    def set_values(self):
        res = super(RegistryConfig, self).set_values()
        self.env["ir.config_parameter"].set_param(
            "g2p_registry.max_registrants_count_job_queue",
            self.max_registrants_count_job_queue,
        )
        self.env["ir.config_parameter"].set_param(
            "g2p_registry.batch_registrants_count_job_queue",
            self.batch_registrants_count_job_queue,
        )
        return res

    @api.model
    def get_values(self):
        res = super(RegistryConfig, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        res.update(
            max_registrants_count_job_queue=params.get_param(
                "g2p_registry.max_registrants_count_job_queue"
            )
        )
        res.update(
            batch_registrants_count_job_queue=params.get_param(
                "g2p_registry.batch_registrants_count_job_queue"
            )
        )
        return res
