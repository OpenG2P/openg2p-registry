from datetime import date, datetime

from pydantic import Field, field_validator

from .naive_orm_model import NaiveOrmModel


class IDType(NaiveOrmModel):
    name: str


class RegistrantIDResponse(NaiveOrmModel):
    id: int
    id_type: str = Field(..., alias="id_type_as_str")
    value: str | None
    expiry_date: date | None = None


class PhoneNumberResponse(NaiveOrmModel):
    id: int
    phone_no: str
    phone_sanitized: str
    date_collected: date | None = None
    # disabled: date | None = None


class PhoneNumberRequest(NaiveOrmModel):
    phone_no: str
    date_collected: str = Field(
        None,
        description="Date of Collected in YYYY-MM-DD format",
        json_schema_extra={"examples": ["2000-01-01"]},
    )

    @field_validator("date_collected")
    @classmethod
    def parse_dob(cls, v):
        if v is None or v == "":
            return None
        return datetime.strptime(v, "%Y-%m-%d").date()


class RegistrantInfoResponse(NaiveOrmModel):
    id: int
    name: str
    ids: list[RegistrantIDResponse] | None = Field([], alias="reg_ids")
    is_group: bool
    registration_date: date | None = None
    phone_numbers: list[PhoneNumberResponse] | None = Field([], alias="phone_number_ids")
    email: str | None = None
    address: str | None = None
    image_1920: bytes | None = None
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
    expiry_date: str = Field(
        None, description="Expiry date in YYYY-MM-DD format", json_schema_extra={"examples": ["2000-01-01"]}
    )
    status: str = None
    description: str = None

    @field_validator("id_type", "value")
    @classmethod
    def check_not_empty(cls, v, field):
        if not v:
            raise ValueError(f"{field} cannot be empty")
        return v

    @field_validator("expiry_date")
    @classmethod
    def parse_dob(cls, v):
        if v is None or v == "":
            return None
        return datetime.strptime(v, "%Y-%m-%d").date()


class RegistrantInfoRequest(NaiveOrmModel):
    name: str = Field(..., description="Mandatory field")
    ids: list[RegistrantIDRequest] | None = None
    registration_date: str = Field(
        None,
        description="Registration date in YYYY-MM-DD format",
        json_schema_extra={"examples": ["2000-01-01"]},
    )
    phone_numbers: list[PhoneNumberRequest] | None = None
    email: str | None = None
    address: str | None = None
    image_1920: bytes | None = None

    @field_validator("registration_date")
    @classmethod
    def parse_dob(cls, v):
        if v is None or v == "":
            return None
        return datetime.strptime(v, "%Y-%m-%d").date()
