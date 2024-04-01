# Part of OpenSPP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class RegistryConfig(models.TransientModel):
    _inherit = "res.config.settings"

    # Job Queue fields
    max_registrants_count_job_queue = fields.Integer(
        "Maximum Registrants Before Using Job Queue",
        config_parameter="g2p_registry.max_registrants_count_job_queue",
    )
    batch_registrants_count_job_queue = fields.Integer(
        "Number of Registrants Per Batch",
        config_parameter="g2p_registry.batch_registrants_count_job_queue",
    )

    phone_regex = fields.Char(config_parameter="g2p_registry.phone_regex")
