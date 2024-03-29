import logging

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel, PydanticModelList
from odoo.addons.component.core import Component

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from ..models.individual import IndividualInfoIn, IndividualInfoOut
from ..models.individual_search_param import IndividualSearchParam
from ..models.registrant import RegistrantUpdateIDIn, RegistrantUpdateIDOut


class IndividualApiService(Component):
    _inherit = ["base.rest.service", "process_individual.rest.mixin"]
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
        partner = self._get(_id)
        if partner:
            return IndividualInfoOut.from_orm(partner)
        else:
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_010.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
                error_description=("Record is not present in the database."),
            )

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
        error_description = ""
        if partner_search_param.name:
            domain.append(("name", "like", partner_search_param.name))
            error_description = "This Name does not exist. Please enter a valid Name."

        if partner_search_param.id:
            domain.append(("id", "=", partner_search_param.id))
            error_description = "The ID Number you have entered does not exist. Please enter a valid ID Number."

        domain.append(("is_registrant", "=", True))
        domain.append(("is_group", "=", False))
        res = []

        for p in self.env["res.partner"].search(domain):
            res.append(IndividualInfoOut.from_orm(p))
        if not len(res):
            if partner_search_param.name and partner_search_param.id:
                error_description = "The ID Number or Name entered does not exist."
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_010.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_010.get_error_code(),
                error_description=error_description,
            )
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
        :return: An instance of partner info
        """
        # Create the individual Object
        indv_rec = self._process_individual(individual_info)

        logging.info("Individual Api: Creating Individual Record")
        indv_id = self.env["res.partner"].create(indv_rec)

        # TODO: Reload the new object from the DB
        partner = self._get(indv_id.id)
        return IndividualInfoOut.from_orm(partner)

    def _get(self, _id):
        partner = self.env["res.partner"].search([("id", "=", _id)])
        if partner and partner.is_registrant and not partner.is_group:
            return partner
        return None

    @restapi.method(
        [("/updateIdentification", "PATCH")],
        input_param=PydanticModel(RegistrantUpdateIDIn),
        output_param=PydanticModel(RegistrantUpdateIDOut),
        auth="user",
    )
    def updateIdentification(self, reg_id):
        """
        Update Individual Identification
        :param reg_id: An instance of the partner.reg_id
        :return: An instance of partner.reg_id
        """
        id_type_id = self.env["g2p.id.type"].search(
            [("name", "=", reg_id.id_type)], limit=1
        )
        if id_type_id:
            registrant = self.env["res.partner"].search(
                [
                    ("id", "=", reg_id.partner_id),
                    ("is_registrant", "=", True),
                    ("is_group", "=", False),
                ]
            )
            if registrant:
                reg_id_dict = reg_id.dict()
                reg_id_dict["id_type"] = id_type_id.id
                for each_reg_id in registrant.reg_ids:
                    if each_reg_id.id_type.id == id_type_id.id:
                        each_reg_id.update(reg_id_dict)
                        return RegistrantUpdateIDOut.from_orm(each_reg_id)
                return RegistrantUpdateIDOut.from_orm(
                    self.env["g2p.reg.id"].create(reg_id_dict)
                )
            else:
                raise G2PApiValidationError(
                    error_message=G2PErrorCodes.G2P_REQ_013.get_error_message(),
                    error_code=G2PErrorCodes.G2P_REQ_013.get_error_code(),
                    error_description=f"The partner ID - {reg_id.partner_id} does not exist.",
                )

        raise G2PApiValidationError(
            error_message=G2PErrorCodes.G2P_REQ_005.get_error_message(),
            error_code=G2PErrorCodes.G2P_REQ_005.get_error_code(),
            error_description=f"The provided ID type - {reg_id.id_type} is Invalid.",
        )
