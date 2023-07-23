from typing import List, Optional

import pydantic
from pydantic import validator

from .group_membership import GroupMembersInfoIn  # fmt: skip
from .group_membership import GroupMembersInfoOut  # fmt: skip
from .registrant import RegistrantInfoIn  # fmt: skip
from .registrant import RegistrantInfoOut  # fmt: skip


class GroupShortInfoOut(RegistrantInfoOut):
    pass


class GroupInfoOut(RegistrantInfoOut):
    is_group = True
    members: List[GroupMembersInfoOut] = pydantic.Field(
        ..., alias="group_membership_ids"
    )
    kind: Optional[str] = pydantic.Field(..., alias="kind_as_str")
    is_partial_group: bool


class GroupInfoIn(RegistrantInfoIn):
    is_group = True
    members: List[GroupMembersInfoIn]
    kind: str = None
    is_partial_group: bool = None

    @validator("kind")
    def validate_kind_no_spaces(cls, value):
        if value and " " in value:
            raise ValueError("Kind field cannot contain spaces.")
        return value
