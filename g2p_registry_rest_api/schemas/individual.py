from datetime import date

from .registrant import RegistrantInfoRequest, RegistrantInfoResponse


class IndividualInfoResponse(RegistrantInfoResponse):
    given_name: str
    addl_name: str | None
    family_name: str
    gender: str = None
    birthdate: date = None
    age: str | None = None
    birth_place: str | None = None
    is_group: bool = False


class IndividualInfoRequest(RegistrantInfoRequest):
    given_name: str
    addl_name: str | None
    family_name: str
    gender: str | None
    birthdate: date | None
    birth_place: str | None
    is_group: bool = False
