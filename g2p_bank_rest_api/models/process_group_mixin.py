from odoo import models


class ProcessGroupMixin(models.AbstractModel):
    _inherit = "process_group.rest.mixin"

    def _process_group(self, group_info):
        res = super()._process_group(group_info)
        if group_info.model_dump().get("bank_ids", None):
            res["bank_ids"] = self._process_bank_ids(group_info)
        return res
