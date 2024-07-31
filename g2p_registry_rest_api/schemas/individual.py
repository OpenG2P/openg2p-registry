from datetime import date, datetime

from pydantic import Field, field_validator

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
    birthdate: str = Field(
        None, description="Date of birth in YYYY-MM-DD format", json_schema_extra={"examples": ["2000-01-01"]}
    )
    birth_place: str | None
    is_group: bool = False

    @field_validator("birthdate")
    @classmethod
    def parse_dob(cls, v):
        if v is None or v == "":
            return None
        return datetime.strptime(v, "%Y-%m-%d").date()


class UpdateIndividualInfoRequest(IndividualInfoRequest):
    updateId: str
    image_1920: bytes | None = None
    given_name: str | None
    name: str | None


class UpdateIndividualInfoResponse(IndividualInfoResponse):
    id: int | None = None
    given_name: str | None = None
    name: str | None = None
    family_name: str | None = None
