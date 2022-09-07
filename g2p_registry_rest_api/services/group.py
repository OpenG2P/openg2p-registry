import logging

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel, PydanticModelList
from odoo.addons.component.core import Component

from ..models.group import GroupInfoIn, GroupInfoOut, GroupShortInfoOut
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
        res = []
        for p in self.env["res.partner"].sudo().search(domain):
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
            individual = membership_info.individual

            logging.info("Name: %s" % individual.name)
            logging.info(dict(individual))

            indv_rec = self._process_individual(individual)

            logging.info("Individual Record to Create: %s" % indv_rec)
            indv_id = self.env["res.partner"].create(indv_rec)

            # Add individual's membership kind fields
            membership_kind = membership_info.kind
            logging.info("membership_kind: %s" % membership_kind)

            indv_membership_kinds = []
            for kind in membership_kind:
                # Search Kind
                kind_id = (
                    self.env["g2p.group.membership.kind"]
                    .sudo()
                    .search([("name", "=", kind.name)])
                )
                if kind_id:
                    kind_id = kind_id[0]
                else:
                    # Create a new Kind
                    kind_id = (
                        self.env["g2p.group.membership.kind"]
                        .sudo()
                        .create({"name": kind.name})
                    )
                indv_membership_kinds.append((4, kind_id.id))
            grp_membership_rec.append(
                {"individual": indv_id.id, "kind": indv_membership_kinds}
            )

        # TODO: create the group object
        logging.info("GROUP:")
        logging.info("Group Name: %s" % group_info.name)

        grp_rec = self._process_group(group_info)

        logging.info("Group Record to Create: %s" % grp_rec)
        grp_id = self.env["res.partner"].create(grp_rec)

        # TODO: Add the relationships
        for mbr in grp_membership_rec:
            mbr_rec = mbr
            mbr_rec.update({"group": grp_id.id})

            logging.info("Membership Record to Create: %s" % mbr_rec)
            self.env["g2p.group.membership"].create(mbr_rec)

        # TODO: Reload the new object from the DB
        partner = self._get(grp_id.id)
        return GroupInfoOut.from_orm(partner)

    # The following method are 'private' and should be never never NEVER call
    # from the controller.

    def _get(self, _id):
        partner = self.env["res.partner"].sudo().browse(_id)
        logging.info("Record to Show: %s" % partner)
        if partner and partner.is_group:
            return partner
        return None

    def _process_individual(self, individual):
        indv_rec = {
            "name": individual.name,
            "registration_date": individual.registration_date,
            "is_registrant": True,
            "is_group": False,
        }

        indv_ids = []
        for indiv_id in individual.ids:
            # Search ID Type
            id_type_id = (
                self.env["g2p.id.type"].sudo().search([("name", "=", indiv_id.id_type)])
            )
            if id_type_id:
                id_type_id = id_type_id[0]
            else:
                # Create a new ID Type
                id_type_id = (
                    self.env["g2p.id.type"].sudo().create({"name": indiv_id.id_type})
                )
            indv_ids.append(
                (
                    0,
                    0,
                    {
                        "id_type": id_type_id.id,
                        "value": indiv_id.value,
                        "expiry_date": indiv_id.expiry_date,
                    },
                )
            )
        if indv_ids:
            indv_rec.update({"reg_ids": indv_ids})

        phone_numbers = []
        for phone in individual.phone_numbers:
            phone_numbers.append(
                (
                    0,
                    0,
                    {
                        "phone_no": phone.phone_no,
                        "date_collected": phone.date_collected,
                    },
                )
            )
        if phone_numbers:
            indv_rec.update({"phone_number_ids": phone_numbers})

        return indv_rec

    def _process_group(self, group_info):
        grp_rec = {
            "name": group_info.name,
            "registration_date": group_info.registration_date,
            "is_registrant": True,
            "is_group": True,
        }
        # Add group's kind field
        if group_info.kind:
            # Search Kind
            kind_id = (
                self.env["g2p.group.kind"]
                .sudo()
                .search([("name", "=", group_info.kind)])
            )
            if kind_id:
                kind_id = kind_id[0]
            else:
                # Create a new Kind
                kind_id = (
                    self.env["g2p.group.kind"].sudo().create({"name": group_info.kind})
                )
                kind_id = kind_id
            grp_rec.update({"kind": kind_id.id})

        grp_ids = []
        for group_id in group_info.ids:
            # Search ID Type
            id_type_id = (
                self.env["g2p.id.type"].sudo().search([("name", "=", group_id.id_type)])
            )
            if id_type_id:
                id_type_id = id_type_id[0]
            else:
                # Create a new ID Type
                id_type_id = (
                    self.env["g2p.id.type"].sudo().create({"name": group_id.id_type})
                )
            grp_ids.append(
                (
                    0,
                    0,
                    {
                        "id_type": id_type_id.id,
                        "value": group_id.value,
                        "expiry_date": group_id.expiry_date,
                    },
                )
            )
        if grp_ids:
            grp_rec.update({"reg_ids": grp_ids})

        phone_numbers = []
        for phone in group_info.phone_numbers:
            phone_numbers.append(
                (
                    0,
                    0,
                    {
                        "phone_no": phone.phone_no,
                        "date_collected": phone.date_collected,
                    },
                )
            )
        if phone_numbers:
            grp_rec.update({"phone_number_ids": phone_numbers})

        return grp_rec
