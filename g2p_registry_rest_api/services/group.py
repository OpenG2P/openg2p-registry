import logging

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel, PydanticModelList
from odoo.addons.component.core import Component

from ..models.group import GroupInfoIn, GroupInfoOut, GroupShortInfoOut
from ..models.group_search_param import GroupSearchParam


class GroupApiService(Component):
    _inherit = ["base.rest.service", "process_group.rest.mixin"]
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
        output_param=PydanticModel(GroupInfoOut),
        auth="user",
    )
    def get(self, _id):
        """
        Get partner's information
        """
        partner = self._get(_id)
        return GroupInfoOut.from_orm(partner)

    @restapi.method(
        [(["/", "/search"], "GET")],
        input_param=PydanticModel(GroupSearchParam),
        output_param=PydanticModelList(GroupShortInfoOut),
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
        domain.append(("is_registrant", "=", True))
        domain.append(("is_group", "=", True))
        res = []

        for p in self.env["res.partner"].search(domain):
            if partner_search_param.include_members_full:
                res.append(GroupInfoOut.from_orm(p))
            else:
                res.append(GroupShortInfoOut.from_orm(p))
        return res

    @restapi.method(
        [(["/"], "POST")],
        input_param=PydanticModel(GroupInfoIn),
        output_param=PydanticModel(GroupInfoOut),
        auth="user",
    )
    def createGroup(self, group_info):
        """
        Create a new Group
        :param group_info: An instance of the group info
        :return: An instance of partner.info
        """
        # Create the individual Objects
        grp_membership_rec = []
        logging.info("INDIVIDUALS:")
        for membership_info in group_info.members:
            individual = membership_info

            indv_rec = self._process_individual(individual)

            logging.info("Creating Individual Record")
            indv_id = self.env["res.partner"].create(indv_rec)

            # Add individual's membership kind fields
            membership_kind = membership_info.kind

            indv_membership_kinds = []
            if membership_kind:
                for kind in membership_kind:
                    # Search Kind
                    kind_id = self.env["g2p.group.membership.kind"].search(
                        [("name", "=", kind.name)]
                    )
                    if kind_id:
                        kind_id = kind_id[0]
                    else:
                        # Create a new Kind
                        kind_id = self.env["g2p.group.membership.kind"].create(
                            {"name": kind.name}
                        )
                    indv_membership_kinds.append((4, kind_id.id))
                grp_membership_rec.append(
                    {"individual": indv_id.id, "kind": indv_membership_kinds}
                )

        # TODO: create the group object
        logging.info("GROUP:")

        grp_rec = self._process_group(group_info)

        logging.info("Creating Group Record")
        grp_id = self.env["res.partner"].create(grp_rec)
        for mbr in grp_membership_rec:
            mbr_rec = mbr
            mbr_rec.update({"group": grp_id.id})

            self.env["g2p.group.membership"].create(mbr_rec)

        # TODO: Reload the new object from the DB
        partner = self._get(grp_id.id)
        return GroupInfoOut.from_orm(partner)

    # The following method are 'private' and should be never never NEVER call
    # from the controller.

    def _get(self, _id):
        partner = self.env["res.partner"].browse(_id)
        if partner and partner.is_group:
            return partner
        return None
