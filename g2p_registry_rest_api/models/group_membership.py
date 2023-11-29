from datetime import date, datetime
from typing import List, Optional

from pydantic import validator

from odoo.http import request

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from .individual import IndividualInfoOut
from .naive_orm_model import NaiveOrmModel
from .registrant import PhoneNumberIn, RegistrantIDIn


class GroupMembershipKindInfo(NaiveOrmModel):
    name: str

    @validator("name")
    def validate_name_no_spaces(cls, value):  # noqa: B902
        # Using lstrip() to remove leading spaces from the value
        new_value = value.lstrip() if value else value

        # Checking if the length of the cleaned value is less than 1
        if value and len(new_value) < 1:
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_001.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_001.get_error_code(),
                error_description="Member's kind field cannot be empty.",
            )
        return value


class GroupMembersInfoOut(NaiveOrmModel):
    id: int
    individual: IndividualInfoOut
    kind: Optional[
        List[GroupMembershipKindInfo]
    ] = None  # TODO: Would be nicer to have it as a list of str
    create_date: datetime = None
    write_date: datetime = None


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

    @validator("gender")
    def validate_gender(cls, value):  # noqa: B902
        options = request.env["gender.type"].search([("active", "=", True)])
        if value and not options.search([("code", "=", value)]):
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_008.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_008.get_error_code(),
                error_description="Invalid gender-%s. It should be %s"
                % (value, [option.code for option in options]),
            )
        return value
