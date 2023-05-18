from odoo.addons.component.core import AbstractComponent


class ProcessIndividualMixin(AbstractComponent):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super(ProcessIndividualMixin, self)._process_individual(individual)
        if individual.dict().get("bank_ids", None):
            res["bank_ids"] = self._process_bank_ids(individual)
        return res

    def _process_bank_ids(self, registrant_info):
        bank_ids = []
        for rec in registrant_info.bank_ids:
            bank_ids.append(
                (
                    0,
                    0,
                    {
                        "acc_number": rec.acc_number,
                    },
                )
            )
        return bank_ids
