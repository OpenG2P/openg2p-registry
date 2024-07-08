from datetime import date, datetime

from .individual import IndividualInfoResponse
from .naive_orm_model import NaiveOrmModel
from .registrant import PhoneNumberRequest, RegistrantIDRequest


class GroupMembershipKindInfo(NaiveOrmModel):
    name: str | None


class GroupMembersInfoResponse(NaiveOrmModel):
    id: int
    individual: IndividualInfoResponse | None = []
    kind: list[GroupMembershipKindInfo] | None = None  # TODO: Would be nicer to have it as a list of str
    create_date: datetime = None
    write_date: datetime = None


class GroupMembersInfoRequest(NaiveOrmModel):
    name: str
    given_name: str = None
    addl_name: str = None
    family_name: str = None
    ids: list[RegistrantIDRequest] = None
    registration_date: date = None
    phone_numbers: list[PhoneNumberRequest] = None
    email: str | None
    address: str | None
    gender: str | None
    birthdate: date = None
    birth_place: str | None
    is_group: bool = False
    kind: list[GroupMembershipKindInfo] = None  # TODO: Would be nicer to have it as a list of str
