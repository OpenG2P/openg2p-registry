import pydantic
from pydantic import validator

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from .group_membership import GroupMembersInfoIn, GroupMembersInfoOut
from .registrant import RegistrantInfoIn, RegistrantInfoOut


class GroupShortInfoOut(RegistrantInfoOut):
    pass


class GroupInfoOut(RegistrantInfoOut):
    is_group = True
    members: list[GroupMembersInfoOut] = pydantic.Field(
        ..., alias="group_membership_ids"
    )
    kind: str | None = pydantic.Field(..., alias="kind_as_str")
    is_partial_group: bool


class GroupInfoIn(RegistrantInfoIn):
    is_group = True
    members: list[GroupMembersInfoIn]
    kind: str = None
    is_partial_group: bool = None

    @validator("kind")
    def validate_kind_no_spaces(cls, value):  # noqa: B902
        # Using lstrip() to remove leading spaces from the value
        new_val = value.lstrip() if value else value

        # Checking if the length of the cleaned value is less than 1
        if value and len(new_val) < 1:
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_001.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_001.get_error_code(),
                error_description="Group type (kind) field cannot be empty.",
            )
        return value
