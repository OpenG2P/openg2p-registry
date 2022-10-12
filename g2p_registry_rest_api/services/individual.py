import logging

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel, PydanticModelList
from odoo.addons.component.core import Component

from ..models.individual import IndividualInfoIn, IndividualInfoOut
from ..models.individual_search_param import IndividualSearchParam
from ..utils.individual_utils import IndividualApiUtils


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
        indv_utils = IndividualApiUtils(self.env)
        partner = indv_utils._get(_id)
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
        res = []

        for p in self.env["res.partner"].search(domain):
            res.append(IndividualInfoOut.from_orm(p))
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
        indv_utils = IndividualApiUtils(self.env)
        indv_rec = indv_utils.process_individual(individual_info)

        logging.info("Individual Api: Creating Individual Record")
        indv_id = self.env["res.partner"].create(indv_rec)
        indv_utils.process_relationship(individual_info.relationships_1, indv_id, 1)
        indv_utils.process_relationship(individual_info.relationships_2, indv_id, 2)

        # TODO: Reload the new object from the DB
        partner = indv_utils._get(indv_id.id)
        return IndividualInfoOut.from_orm(partner)
