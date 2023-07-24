from datetime import date
from typing import List

import pydantic
from pydantic import validator

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
    def validate_id_type_no_spaces(cls, value):
        # Using lstrip() to remove leading spaces from the value
        value = value.lstrip() if value else value

        # Checking if the length of the cleaned value is less than 1
        if len(value) < 1:
            raise ValueError("ID type cannot be empty or contain only spaces.")
        return value


class RegistrantInfoIn(NaiveOrmModel):
    name: str
    ids: List[RegistrantIDIn] = None
    registration_date: date = None
    is_group: bool
    phone_numbers: List[PhoneNumberIn] = None
    email: str = None
    address: str = None


class RegistrantUpdateIDIn(RegistrantIDIn):
    partner_id: int


class RegistrantUpdateIDOut(RegistrantIDOut):
    partner_id: int
