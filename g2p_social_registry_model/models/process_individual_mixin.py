from odoo import models


class ProcessSocialIndividualMixin(models.AbstractModel):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super()._process_individual(individual)
        info_dict = individual.model_dump()

        individual_fields = [
            "education_level",
            "employment_status",
            "marital_status",
            "occupation",
            "income",
        ]

        for field in individual_fields:
            if info_dict.get(field):
                res[field] = info_dict[field]

        return res
