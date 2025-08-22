# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from . import models


def _uninstall_cleanup(env):
    parameter_keys = [
        "g2p_registry_id_deduplication.grp_deduplication_id_types_ids",
        "g2p_registry_id_deduplication.ind_deduplication_id_types_ids",
    ]

    for key in parameter_keys:
        env["ir.config_parameter"].sudo().set_param(key, None)
