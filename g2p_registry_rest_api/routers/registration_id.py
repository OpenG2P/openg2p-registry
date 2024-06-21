import logging
from datetime import date

from typing import Annotated
from fastapi import APIRouter, Depends
from odoo.api import Environment
from odoo.addons.fastapi.dependencies import odoo_env
from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from ..schemas.registration_id import RegistrationIDResponse,UpdateRegistrantInfoRequest

rid_router = APIRouter(tags=["Registration id"])

update_registrant_router = APIRouter(tags=["Update Registrant using rid"])


# Fetch registration IDs
@rid_router.get(
    "/get/rids",
    responses={200: {"model": list[str]}},
)
async def fetch_registration_ids(
    env: Annotated[Environment, Depends(odoo_env)],
    id_type: str,
):
    """
    Fetch the registration IDs of all registrants
    """
    try:
        if not id_type:
            _handle_error(G2PErrorCodes.G2P_REQ_010, "Record is not present in the database.")

        id_type_rec = env["g2p.reg.id"].sudo().search([("id_type.name", "=", id_type)])
        registration_ids = [rec.value for rec in id_type_rec]
        return registration_ids
    except Exception as e:
        logging.error(f"Error fetching registration IDs: {str(e)}")
        _handle_error(G2PErrorCodes.G2P_REQ_010, "An error occurred while fetching registration IDs.")


# Update partner using registration ID
@update_registrant_router.put(
    "/update/partner",
)
async def update_partner_using_rid(
    env: Annotated[Environment, Depends(odoo_env)],
    requests: list[UpdateRegistrantInfoRequest],
):
    """
    Update partner records using registration IDs
    """
    results = []

    for request in requests:
        try:
            update_data = {}
            logging.info(f"Request data: {request}")
            registration_id = request.registrationId
            if registration_id:
                partner_rec = env["res.partner"].sudo().search([("reg_ids.value", "=", registration_id)], limit=1)
                if not partner_rec:
                    _handle_error(G2PErrorCodes.G2P_REQ_010, f"Partner with the given registration ID {registration_id} not found.")

                if request.name is not None:
                    name_parts = request.name.split(" ")
                    update_data["given_name"] = name_parts[0]
                    update_data["family_name"] = name_parts[-1]
                    update_data["addl_name"] = " ".join(name_parts[1:-1])
                    update_data["name"] = request.name

                if request.birthdate is not None and request.birthdate != date.today():
                    update_data["birthdate"] = request.birthdate
                if request.gender is not None:
                    update_data["gender"] = _process_gender(env, request.gender)
                if request.birth_place is not None:
                    update_data["birth_place"] = request.birth_place
                if request.email is not None:
                    update_data["email"] = request.email
                if request.address is not None:
                    update_data["address"] = request.address

                 # Process faydaId mapping
                
                fayda_value = None
                if request.faydaId is not None:
                    for fayda in request.faydaId:
                        id_type = fayda.id_type
                        fayda_value = fayda.value
                        if id_type and fayda_value:
                            available_id = env["res.partner"].sudo().search([("reg_ids.value", "=", fayda_value)], limit=1)
                            if not available_id:
                                partner_rec.reg_ids =  _process_ids(env, id_type, fayda_value)

                partner_rec.write(update_data)
                results.append({"faydaId": fayda_value if fayda_value else None, "registrationId": registration_id, "status": "Success", "message": "Partner data's updated successfully"})

            else:
                logging.error("Registration ID is required")
                _handle_error(G2PErrorCodes.G2P_REQ_010, "Registration ID is required")

        except Exception as e:
            logging.error(f"Error occurred while updating the partner with registration ID {request.registrationId}: {str(e)}")
            results.append({"registrationId": request.registrationId, "status": "Error", "message": str(e)})

    return results

def _handle_error(error_code, error_description):
    raise G2PApiValidationError(
        error_message=error_code.get_error_message(),
        error_code=error_code.get_error_code(),
        error_description=error_description,
    )

def _process_gender(env,gender):
        gender = (
            env["gender.type"]
            .sudo()
            .search([("active", "=", True), ("code", "=",gender)], limit=1)
        )
        if gender:
            return gender.value
        return None


def _process_ids(env,id_type,value):
    ids = []
    if id_type and value:
        # Search ID Type
        id_type_id = env["g2p.id.type"].sudo().search([("name", "=", id_type)],limit=1)
        if id_type_id:
            ids.append(
                (
                    0,
                    0,
                    {
                        "id_type": id_type_id[0].id,
                        "value": value,
                    },
                )
            )

        else:
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_005.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_005.get_error_code(),
                error_description=(("ID type - %s is not present in the database.") % id_type)
            )

        return ids