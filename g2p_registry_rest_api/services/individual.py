import logging

from werkzeug.exceptions import NotFound

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel, PydanticModelList
from odoo.addons.component.core import Component

from ..models.individual import IndividualInfoIn, IndividualInfoOut
from ..models.individual_search_param import IndividualSearchParam


class IndividualApiService(Component):
    _inherit = "base.rest.service"
    _name = "registrant_individual.rest.service"
    _usage = "individual"
    _collection = "base.rest.registry.services"
    _description = """
        Registrant Individual API Services
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
        output_param=PydanticModel(IndividualInfoOut),
        auth="user",
    )
    def get(self, _id):
        """
        Get partner's information
        """
        indv_helper = self.env["registrant_individual.rest.service.helper"]
        partner = indv_helper._get(_id)
        if not partner:
            raise NotFound()
        return IndividualInfoOut.from_orm(partner)

    @restapi.method(
        [(["/", "/search"], "GET")],
        input_param=PydanticModel(IndividualSearchParam),
        output_param=PydanticModelList(IndividualInfoOut),
        auth="user",
    )
    def search(self, partner_search_param):
        """
        Search for partners
        :param partner_search_param: An instance of partner.search.param
        :return: List of partner.info
        """
        domain = []
        if partner_search_param.name:
            domain.append(("name", "like", partner_search_param.name))
        if partner_search_param.id:
            domain.append(("id", "=", partner_search_param.id))
        domain.append(("is_registrant", "=", True))
        domain.append(("is_group", "=", False))
        res = []

        for p in self.env["res.partner"].search(domain):
            res.append(IndividualInfoOut.from_orm(p))
        if not res:
            raise NotFound()
        return res

    @restapi.method(
        [(["/"], "POST")],
        input_param=PydanticModel(IndividualInfoIn),
        output_param=PydanticModel(IndividualInfoOut),
        auth="user",
    )
    def createIndividual(self, individual_info):
        """
        Create a new Individual
        :param individual_info: An instance of the individual info
        :return: An instance of partner.info
        """
        # Create the individual Object
        indv_helper = self.env["registrant_individual.rest.service.helper"]
        indv_rec = indv_helper.process_individual(individual_info)

        logging.info("Individual Api: Creating Individual Record")
        indv_id = self.env["res.partner"].create(indv_rec)

        # TODO: Reload the new object from the DB
        partner = indv_helper._get(indv_id.id)
        return IndividualInfoOut.from_orm(partner)
