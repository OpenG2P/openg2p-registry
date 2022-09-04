from datetime import date
from typing import List

import pydantic

from .naive_orm_model import NaiveOrmModel


class IDType(NaiveOrmModel):
    name: str


class RegistrantID(NaiveOrmModel):
    id: int
    id_type: str = pydantic.Field(..., alias="id_type_as_str")
    value: str
    expiry_date: date = None


class PhoneNumber(NaiveOrmModel):
    id: int
    phone_no: str
    phone_sanitized: str
    date_collected: date
    disabled: date = None


class RegistrantInfo(NaiveOrmModel):
    id: int
    name: str
    ids: List[RegistrantID] = pydantic.Field(..., alias="reg_ids")
    is_group: bool
    registration_date: date = None
    phone_numbers: List[PhoneNumber] = pydantic.Field(..., alias="phone_number_ids")
