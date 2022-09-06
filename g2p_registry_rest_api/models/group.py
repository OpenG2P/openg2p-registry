from typing import List

import pydantic

from .group_membership import GroupMembersInfoIn
from .registrant import RegistrantInfoIn, RegistrantInfoOut


class GroupShortInfoOut(RegistrantInfoOut):
    pass


class GroupInfoOut(RegistrantInfoOut):
    is_group = True
    # members: List[GroupMembersInfoOut] = pydantic.Field(
    #    ..., alias="group_membership_ids"
    # )
    kind: str = pydantic.Field(..., alias="kind_as_str")


class GroupInfoIn(RegistrantInfoIn):
    is_group = True
    members: List[GroupMembersInfoIn]
    kind: str
