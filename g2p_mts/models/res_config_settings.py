import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    g2p_mts_vid_delete_job_status = fields.Boolean(
        default=lambda x: x.env.ref("g2p_mts.to_delete_g2p_reg_id_vid").active
    )
    g2p_mts_vid_delete_search_domain = fields.Char(config_parameter="g2p_mts.vid_delete_search_domain")

    g2p_mts_vid_id_type = fields.Many2one("g2p.id.type", config_parameter="g2p_mts.vid_id_type")
    g2p_mts_uin_token_id_type = fields.Many2one("g2p.id.type", config_parameter="g2p_mts.uin_token_id_type")

    @api.constrains("g2p_mts_vid_delete_job_status")
    def _constrains_vehicle(self):
        self.env.ref("g2p_mts.to_delete_g2p_reg_id_vid").active = self.g2p_mts_vid_delete_job_status
