from typing import List

import pydantic

from .group_membership import GroupMembersInfo
from .registrant import RegistrantInfo


class GroupShortInfo(RegistrantInfo):
    pass


class GroupInfo(RegistrantInfo):
    members: List[GroupMembersInfo] = pydantic.Field(..., alias="group_membership_ids")
