from odoo.addons.component.core import AbstractComponent


class ProcessGroupMixin(AbstractComponent):
    _inherit = "process_group.rest.mixin"

    def _process_group(self, group_info):
        res = super(ProcessGroupMixin, self)._process_group(group_info)
        if group_info.dict().get("bank_ids", None):
            res["bank_ids"] = self._process_bank_ids(group_info)
        return res
