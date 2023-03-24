from odoo.addons.component.core import AbstractComponent


class ProcessIndividualMixin(AbstractComponent):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super(ProcessIndividualMixin, self)._process_individual(individual)
        if individual.dict().get("additional_g2p_info", None):
            res["additional_g2p_info"] = individual.additional_g2p_info
        return res
