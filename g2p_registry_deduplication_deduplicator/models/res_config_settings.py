# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    deduplicator_config_id = fields.Many2one(
        "g2p.registry.deduplication.deduplicator.config",
        config_parameter="g2p_registry_deduplication_deduplicator.deduplicator_config_id",
    )
