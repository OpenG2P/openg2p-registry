from datetime import date, datetime

import pydantic
from pydantic import Field, field_validator

from .naive_orm_model import NaiveOrmModel


class IDType(NaiveOrmModel):
    name: str


class RegistrantIDResponse(NaiveOrmModel):
    id: int
    id_type: str = pydantic.Field(..., alias="id_type_as_str")
    value: str | None
    expiry_date: date | bool | None = None


class PhoneNumberResponse(NaiveOrmModel):
    id: int
    phone_no: str
    phone_sanitized: str
    date_collected: date = None
    # disabled: date | None = None


class PhoneNumberRequest(NaiveOrmModel):
    phone_no: str
    date_collected: date = None


class RegistrantInfoResponse(NaiveOrmModel):
    id: int
    name: str
    ids: list[RegistrantIDResponse] | None = pydantic.Field([], alias="reg_ids")
    is_group: bool
    registration_date: date = None
    phone_numbers: list[PhoneNumberResponse] | None = pydantic.Field([], alias="phone_number_ids")
    email: str | bool | None = None
    address: str | bool | None = None
    create_date: datetime = None
    write_date: datetime = None

    @field_validator("email", "address")
    @classmethod
    def validate_email(cls, v):
        if v is False:
            return ""


class RegistrantIDRequest(NaiveOrmModel):
    id_type: str
    value: str
    expiry_date: date | None = None


class RegistrantInfoRequest(NaiveOrmModel):
    name: str = Field(..., description="Mandatory field")
    ids: list[RegistrantIDRequest]
    registration_date: date = None
    phone_numbers: list[PhoneNumberRequest] | None = None
    email: str | None = None
    address: str | None = None
