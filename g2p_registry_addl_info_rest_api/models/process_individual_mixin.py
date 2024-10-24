from odoo import models


class ProcessIndividualMixin(models.AbstractModel):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super()._process_individual(individual)
        if individual.dict().get("additional_g2p_info", None):
            res["additional_g2p_info"] = individual.additional_g2p_info
        return res
