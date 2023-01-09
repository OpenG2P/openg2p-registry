from typing import List, Optional

from .individual import IndividualInfoIn, IndividualInfoOut
from .naive_orm_model import NaiveOrmModel


class GroupMembershipKindInfo(NaiveOrmModel):
    name: str


class GroupMembersInfoOut(NaiveOrmModel):
    id: int
    individual: IndividualInfoOut
    kind: Optional[
        List[GroupMembershipKindInfo]
    ] = None  # TODO: Would be nicer to have it as a list of str


class GroupMembersInfoIn(IndividualInfoIn):
    kind: List[
        GroupMembershipKindInfo
    ] = None  # TODO: Would be nicer to have it as a list of str
