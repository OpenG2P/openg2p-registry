from werkzeug.exceptions import BadRequest

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..models.registrant import RegistrantIDIn, RegistrantIDOut


class RegistrantUpdateIDIn(RegistrantIDIn):
    partner_id: int


class RegistrantUpdateIDOut(RegistrantIDOut):
    partner_id: int


class IndividualApiServiceUpdateId(Component):
    _inherit = "registrant_individual.rest.service"

    @restapi.method(
        [("/updateIdentification", "PUT")],
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
        id_type_id = self.env["g2p.id.type"].search([("name", "=", reg_id.id_type)])
        if id_type_id:
            id_type_id = id_type_id[0]
            registrant = self.env["res.partner"].search(
                [("id", "=", reg_id.partner_id)]
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
        raise BadRequest()
