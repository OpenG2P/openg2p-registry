from datetime import date
from typing import Annotated
from .registrant import IDType

from .naive_orm_model import NaiveOrmModel


class RegistrationIDRequest(NaiveOrmModel):
    id_type: str

class RegistrationIDResponse(NaiveOrmModel):
    value: list[str]


class IDRequest(NaiveOrmModel):
    id_type: str = ""
    value: str = ""

class UpdateRegistrantInfoRequest(NaiveOrmModel):
    registrationId: str
    faydaId: list[IDRequest] | None
    name: str = ""
    gender: str = ""
    birthdate: date | None=None
    birth_place: str = ""
    email: str = ""
    address: str = ""

