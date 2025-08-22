# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import safe_eval


class RegistryConfig(models.TransientModel):
    _inherit = "res.config.settings"

    grp_deduplication_id_types_ids = fields.Many2many(
        "g2p.group.kind.deduplication.config",
    )

    ind_deduplication_id_types_ids = fields.Many2many(
        "g2p.id.type",
        "g2p_registry_id_ind_deduplcation_rel",
    )

    def set_values(self):
        res = super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "g2p_registry_id_deduplication.grp_deduplication_id_types_ids",
            self.grp_deduplication_id_types_ids.ids,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "g2p_registry_id_deduplication.ind_deduplication_id_types_ids",
            self.ind_deduplication_id_types_ids.ids,
        )
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        ir_config = self.env["ir.config_parameter"].sudo()
        grp_id_types = ir_config.get_param("g2p_registry_id_deduplication.grp_deduplication_id_types_ids")
        ind_id_types = ir_config.get_param("g2p_registry_id_deduplication.ind_deduplication_id_types_ids")
        res.update(
            grp_deduplication_id_types_ids=[(6, 0, safe_eval.safe_eval(grp_id_types))]
            if grp_id_types
            else None,
            ind_deduplication_id_types_ids=[(6, 0, safe_eval.safe_eval(ind_id_types))]
            if ind_id_types
            else None,
        )
        return res


class G2PIDType(models.Model):
    _inherit = "g2p.id.type"

    def unlink(self):
        ids_to_delete = self.ids

        res = super().unlink()

        ir_config = self.env["ir.config_parameter"].sudo()
        ind_id_types_param = ir_config.get_param(
            "g2p_registry_id_deduplication.ind_deduplication_id_types_ids"
        )

        if ind_id_types_param:
            ind_id_types_ids = safe_eval.safe_eval(ind_id_types_param)
            updated_ind_id_types_ids = [
                id_type for id_type in ind_id_types_ids if id_type not in ids_to_delete
            ]
            ir_config.set_param(
                "g2p_registry_id_deduplication.ind_deduplication_id_types_ids",
                updated_ind_id_types_ids,
            )

        return res
