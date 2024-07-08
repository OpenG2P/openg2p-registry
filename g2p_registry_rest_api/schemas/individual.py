from datetime import date

from pydantic import field_validator

from .registrant import RegistrantInfoRequest, RegistrantInfoResponse


class IndividualInfoResponse(RegistrantInfoResponse):
    given_name: str
    addl_name: str | bool | None = None
    family_name: str
    gender: str | bool | None = None
    birthdate: date | bool | None = None
    age: str | None = None
    birth_place: str | bool | None = None
    is_group: bool = False

    @field_validator("addl_name", "gender", "birthdate", "birth_place", "email", "address")
    @classmethod
    def validate_email(cls, v):
        if v is False:
            return ""


class IndividualInfoRequest(RegistrantInfoRequest):
    given_name: str
    addl_name: str | None = None
    family_name: str | None = None
    gender: str | None
    birthdate: date | None
    birth_place: str | None
    is_group: bool = False


class UpdateIndividualInfoRequest(IndividualInfoRequest):
    updateId: str
