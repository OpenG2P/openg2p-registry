from datetime import date
from typing import List

import pydantic

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
    date_collected: date
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


class RegistrantIDIn(NaiveOrmModel):
    id_type: str
    value: str
    expiry_date: date = None


class RegistrantInfoIn(NaiveOrmModel):
    name: str
    ids: List[RegistrantIDIn]
    registration_date: date = None
    phone_numbers: List[PhoneNumberIn]
