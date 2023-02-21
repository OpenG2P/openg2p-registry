from odoo.addons.component.core import AbstractComponent


class ProcessGroupMixin(AbstractComponent):
    _inherit = "process_group.rest.mixin"

    def _process_group(self, group_info):
        res = super(ProcessGroupMixin, self)._process_group(group_info)
        if group_info.dict().get("additional_g2p_info", None):
            res["additional_g2p_info"] = group_info.additional_g2p_info
        return res
