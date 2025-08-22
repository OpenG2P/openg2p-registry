from odoo import models


class ProcessSocialGroupMixin(models.AbstractModel):
    _inherit = "process_group.rest.mixin"

    def _process_group(self, group_info):
        res = super()._process_group(group_info)
        info_dict = group_info.model_dump()

        social_fields = [
            "num_preg_lact_women",
            "num_malnourished_children",
            "num_disabled",
            "type_of_disability",
            "caste_ethnic_group",
            "belong_to_protected_groups",
            "other_vulnerable_status",
        ]

        economic_fields = [
            "income_sources",
            "annual_income",
            "owns_two_wheeler",
            "owns_three_wheeler",
            "owns_four_wheeler",
            "owns_cart",
            "land_ownership",
            "type_of_land_owned",
            "land_size",
            "owns_house",
            "owns_livestock",
        ]

        for field in social_fields + economic_fields:
            if info_dict.get(field):
                res[field] = info_dict[field]

        return res
