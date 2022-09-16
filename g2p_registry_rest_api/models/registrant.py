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
    date_collected: date = None
    disabled: date = None


class PhoneNumberIn(NaiveOrmModel):
    phone_no: str
    date_collected: date = None


class Relationship1Out(NaiveOrmModel):
    id: int
    registrant: int = pydantic.Field(..., alias="source")
    relation: str = pydantic.Field(..., alias="relation_as_str")


class Relationship2Out(NaiveOrmModel):
    id: int
    registrant: int = pydantic.Field(..., alias="destination")
    relation: str = pydantic.Field(..., alias="relation_as_str")


class RegistrantInfoOut(NaiveOrmModel):
    id: int
    name: str
    given_name: str = None
    family_name: str = None
    gender: str = None
    birthdate: date = None
    age: str
    birth_place: str = None
    ids: List[RegistrantIDOut] = pydantic.Field(..., alias="reg_ids")
    is_group: bool
    registration_date: date = None
    phone_numbers: List[PhoneNumberOut] = pydantic.Field(..., alias="phone_number_ids")
    email: str = None
    address: str = None


class RegistrantIDIn(NaiveOrmModel):
    id_type: str
    value: str
    expiry_date: date = None


class RegistrantInfoIn(NaiveOrmModel):
    name: str
    given_name: str = None
    family_name: str = None
    gender: str = None
    birthdate: date = None
    birth_place: str = None
    ids: List[RegistrantIDIn]
    registration_date: date = None
    is_group: bool
    phone_numbers: List[PhoneNumberIn]
    email: str = None
    address: str = None


class Relationship1In(NaiveOrmModel):
    registrant: int
    relation: str


class Relationship2In(NaiveOrmModel):
    registrant: int
    relation: str
