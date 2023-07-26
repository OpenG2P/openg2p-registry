from datetime import date
from typing import List, Optional

from pydantic import validator

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from .individual import IndividualInfoOut
from .naive_orm_model import NaiveOrmModel
from .registrant import PhoneNumberIn, RegistrantIDIn


class GroupMembershipKindInfo(NaiveOrmModel):
    name: str

    @validator("name")
    def validate_name_no_spaces(cls, value):
        # Using lstrip() to remove leading spaces from the value
        value = value.lstrip() if value else value

        # Checking if the length of the cleaned value is less than 1
        if len(value) < 1:
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_001.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_001.get_error_code(),
                error_description="Member's Kind field cannot be empty.",
            )
        return value


class GroupMembersInfoOut(NaiveOrmModel):
    id: int
    individual: IndividualInfoOut
    kind: Optional[
        List[GroupMembershipKindInfo]
    ] = None  # TODO: Would be nicer to have it as a list of str


class GroupMembersInfoIn(NaiveOrmModel):
    name: str
    given_name: str = None
    addl_name: str = None
    family_name: str = None
    ids: List[RegistrantIDIn] = None
    registration_date: date = None
    phone_numbers: List[PhoneNumberIn] = None
    email: str = None
    address: str = None
    gender: str = None
    birthdate: date = None
    birth_place: str = None
    is_group = False
    kind: List[
        GroupMembershipKindInfo
    ] = None  # TODO: Would be nicer to have it as a list of str
