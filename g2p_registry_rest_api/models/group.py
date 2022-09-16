from typing import List

import pydantic

from .group_membership import GroupMembersInfoIn  # fmt: skip
from .group_membership import GroupMembersInfoOut  # fmt: skip
from .registrant import RegistrantInfoIn  # fmt: skip
from .registrant import RegistrantInfoOut  # fmt: skip
from .registrant import Relationship1In  # fmt: skip
from .registrant import Relationship1Out  # fmt: skip
from .registrant import Relationship2In  # fmt: skip
from .registrant import Relationship2Out  # fmt: skip


class GroupShortInfoOut(RegistrantInfoOut):
    relationships_1: List[Relationship1Out] = pydantic.Field(..., alias="related_1_ids")
    relationships_2: List[Relationship2Out] = pydantic.Field(..., alias="related_2_ids")


class GroupInfoOut(RegistrantInfoOut):
    is_group = True
    members: List[GroupMembersInfoOut] = pydantic.Field(
        ..., alias="group_membership_ids"
    )
    kind: str = pydantic.Field(..., alias="kind_as_str")
    relationships_1: List[Relationship1Out] = pydantic.Field(..., alias="related_1_ids")
    relationships_2: List[Relationship2Out] = pydantic.Field(..., alias="related_2_ids")
    is_partial_group: bool


class GroupInfoIn(RegistrantInfoIn):
    is_group = True
    members: List[GroupMembersInfoIn]
    kind: str
    relationships_1: List[Relationship1In]
    relationships_2: List[Relationship2In]
    is_partial_group: bool
