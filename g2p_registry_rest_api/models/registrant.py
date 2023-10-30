import re
from datetime import date
from typing import List

import pydantic
from pydantic import validator

from odoo import tools
from odoo.http import request

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from .naive_orm_model import NaiveOrmModel


class IDType(NaiveOrmModel):
    name: str


class RegistrantIDOut(NaiveOrmModel):
    id: int
    id_type: str = pydantic.Field(..., alias="id_type_as_str")
    value: str
    expiry_date: date = None


class PhoneNumberOut(NaiveOrmModel):
    id: int
    phone_no: str
    phone_sanitized: str
    date_collected: date = None
    disabled: date = None


class PhoneNumberIn(NaiveOrmModel):
    phone_no: str
    date_collected: date = None

    @validator("phone_no")
    def validate_phone_number(cls, value):  # noqa: B902
        phone_number_pattern = request.env["ir.config_parameter"].get_param(
            "g2p_registry.phone_regex"
        )
        if value and not re.match(phone_number_pattern, value):
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_006.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_006.get_error_code(),
                error_description=("Please provide a valid phone number"),
            )
        return value


class RegistrantInfoOut(NaiveOrmModel):
    id: int
    name: str
    ids: List[RegistrantIDOut] = pydantic.Field(..., alias="reg_ids")
    is_group: bool
    registration_date: date = None
    phone_numbers: List[PhoneNumberOut] = pydantic.Field(..., alias="phone_number_ids")
    email: str = None
    address: str = None


class RegistrantIDIn(NaiveOrmModel):
    id_type: str = None
    value: str = None
    expiry_date: date = None

    @validator("id_type")
    def validate_id_type_no_spaces(cls, value):  # noqa: B902
        # Using lstrip() to remove leading spaces from the value
        new_val = value.lstrip() if value else value

        # Checking if the length of the cleaned value is less than 1
        if value and len(new_val) < 1:
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_005.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_005.get_error_code(),
                error_description="ID type field cannot be empty.",
            )
        return value

    @validator("value")
    def validate_id_value(cls, value, values):
        id_type = values.get("id_type")
        if id_type:
            id_type_id = request.env["g2p.id.type"].search(
                [("name", "=", id_type)], limit=1
            )
            if not re.match(id_type_id.id_validation, value):
                raise G2PApiValidationError(
                    error_message=G2PErrorCodes.G2P_REQ_005.get_error_message(),
                    error_code=G2PErrorCodes.G2P_REQ_005.get_error_code(),
                    error_description=f"The provided {id_type_id.name} ID '{value}' is invalid.",
                )

        return value


class RegistrantInfoIn(NaiveOrmModel):
    name: str
    ids: List[RegistrantIDIn] = None
    registration_date: date = None
    is_group: bool
    phone_numbers: List[PhoneNumberIn] = None
    email: str = None
    address: str = None

    @validator("email")
    def validate_email(cls, value):  # noqa: B902
        if value and not tools.single_email_re.match(value):
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_007.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_007.get_error_code(),
                error_description=("Please provide a valid email address"),
            )
        return value


class RegistrantUpdateIDIn(RegistrantIDIn):
    partner_id: int


class RegistrantUpdateIDOut(RegistrantIDOut):
    partner_id: int
