import json

from odoo import models


class IndividualApiHelper(models.AbstractModel):
    _name = "registrant_individual.rest.service.helper"

    def _get(self, _id):
        partner = self.env["res.partner"].browse(_id)
        if partner and partner.is_registrant and not partner.is_group:
            return partner
        return None

    def process_individual(self, individual):
        indv_rec = {
            "name": self.process_name(
                individual.family_name, individual.given_name, individual.addl_name
            ),
            "registration_date": individual.registration_date,
            "is_registrant": True,
            "is_group": False,
            "email": individual.email,
            "given_name": individual.given_name,
            "family_name": individual.family_name,
            "addl_name": individual.addl_name,
            "gender": individual.gender.capitalize() or False,
            "birthdate": individual.birthdate or False,
            "birth_place": individual.birth_place or False,
            "address": individual.address or None,
            "additional_g2p_info": json.dumps(
                individual.addl_info, separators=(",", ":")
            ),
        }

        ids = []
        ids_info = individual
        ids = self.process_ids(ids_info)

        if ids:
            indv_rec.update({"reg_ids": ids})

        phone_numbers = []
        phone_numbers, primary_phone = self.process_phones(ids_info)

        if primary_phone:
            indv_rec.update({"phone": primary_phone})
        if phone_numbers:
            indv_rec.update({"phone_number_ids": phone_numbers})

        return indv_rec

    def process_name(self, family_name, given_name, addl_name):
        name = ""
        if family_name:
            name += family_name + ", "
        if given_name:
            name += given_name + " "
        if addl_name:
            name += addl_name + " "
        return name.upper()

    def process_ids(self, ids_info):
        ids = []
        if ids_info.ids:
            for rec in ids_info.ids:
                # Search ID Type
                id_type_id = self.env["g2p.id.type"].search(
                    [("name", "=", rec.id_type)]
                )
                if id_type_id:
                    id_type_id = id_type_id[0]
                else:
                    # Create a new ID Type
                    id_type_id = self.env["g2p.id.type"].create({"name": rec.id_type})
                ids.append(
                    (
                        0,
                        0,
                        {
                            "id_type": id_type_id.id,
                            "value": rec.value,
                            "expiry_date": rec.expiry_date,
                            "status": rec.status,
                            "error": rec.error,
                        },
                    )
                )
            return ids

    def process_phones(self, ids_info):
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
