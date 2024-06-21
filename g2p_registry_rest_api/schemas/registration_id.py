from datetime import date

from .naive_orm_model import NaiveOrmModel


class IDRequest(NaiveOrmModel):
    id_type: str = ""
    value: str = ""


class UpdateRegistrantInfoRequest(NaiveOrmModel):
    registrationId: str
    faydaId: IDRequest | None
    name: str = ""
    gender: str | None = ""
    birthdate: date | None = None
    email: str | None = ""
    address: str | None = ""
