from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel, PydanticModelList
from odoo.addons.component.core import Component

from ..models.group import GroupInfo, GroupShortInfo
from ..models.group_search_param import GroupSearchParam


class GroupApiService(Component):
    _inherit = "base.rest.service"
    _name = "registrant_group.rest.service"
    _usage = "group"
    _collection = "base.rest.registry.services"
    _description = """
        Registrant Group API Services
    """

    @restapi.method(
        [
            (
                [
                    "/<int:id>",
                ],
                "GET",
            )
        ],
        output_param=PydanticModel(GroupInfo),
        auth="user",
    )
    def get(self, _id):
        """
        Get partner's information
        """
        partner = self._get(_id)
        return GroupInfo.from_orm(partner)

    @restapi.method(
        [(["/", "/search"], "GET")],
        input_param=PydanticModel(GroupSearchParam),
        output_param=PydanticModelList(GroupShortInfo),
        auth="user",
    )
    def search(self, partner_search_param):
        """
        Search for partners
        :param partner_search_param: An instance of partner.search.param
        :return: List of partner.short.info
        """
        domain = []
        if partner_search_param.name:
            domain.append(("name", "like", partner_search_param.name))
        if partner_search_param.id:
            domain.append(("id", "=", partner_search_param.id))
        res = []
        for p in self.env["res.partner"].sudo().search(domain):
            res.append(GroupShortInfo.from_orm(p))
        return res

    # The following method are 'private' and should be never never NEVER call
    # from the controller.

    def _get(self, _id):
        partner = self.env["res.partner"].sudo().browse(_id)
        if partner and partner.is_group:
            return partner
        return None
