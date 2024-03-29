from odoo.addons.component.core import AbstractComponent

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes


class ProcessIndividualMixin(AbstractComponent):
    _name = "process_individual.rest.mixin"
    _description = """
        Process Individual REST API Mixin
    """

    def _process_individual(self, individual):
        indv_rec = {
            "name": individual.name,
            "registration_date": individual.registration_date,
            "is_registrant": True,
            "is_group": False,
            "email": individual.email,
            "given_name": individual.given_name,
            "family_name": individual.family_name,
            "addl_name": individual.addl_name,
            "birthdate": individual.birthdate or False,
            "birth_place": individual.birth_place or False,
            "address": individual.address or None,
        }

        ids = []
        ids_info = individual
        ids = self._process_ids(ids_info)

        if ids:
            indv_rec.update({"reg_ids": ids})

        phone_numbers = []
        phone_numbers, primary_phone = self._process_phones(ids_info)

        if primary_phone:
            indv_rec.update({"phone": primary_phone})
        if phone_numbers:
            indv_rec.update({"phone_number_ids": phone_numbers})

        gender = self._process_gender(ids_info)
        if gender:
            indv_rec.update({"gender": gender})
        return indv_rec

    def _process_ids(self, ids_info):
        ids = []
        if ids_info.ids:
            for rec in ids_info.ids:
                # Search ID Type
                id_type_id = self.env["g2p.id.type"].search(
                    [("name", "=", rec.id_type)]
                )
                if id_type_id:
                    ids.append(
                        (
                            0,
                            0,
                            {
                                "id_type": id_type_id[0].id,
                                "value": rec.value,
                                "expiry_date": rec.expiry_date,
                            },
                        )
                    )

                elif rec.id_type:
                    raise G2PApiValidationError(
                        error_message=G2PErrorCodes.G2P_REQ_005.get_error_message(),
                        error_code=G2PErrorCodes.G2P_REQ_005.get_error_code(),
                        error_description=(
                            ("ID type - %s is not present in the database.")
                            % rec.id_type
                        ),
                    )

            return ids

    def _process_phones(self, ids_info):
        primary_phone = None
        phone_numbers = []
        if ids_info.phone_numbers:
            for phone in ids_info.phone_numbers:
                if phone.phone_no and not primary_phone:
                    primary_phone = phone.phone_no
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
        return phone_numbers, primary_phone

    def _process_gender(self, ids_info):
        if ids_info.gender:
            gender = self.env["gender.type"].search(
                [("active", "=", True), ("code", "=", ids_info.gender)], limit=1
            )
            if gender:
                return gender.value
        return None
