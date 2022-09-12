from typing import List

from .individual import IndividualInfoIn, IndividualInfoOut
from .naive_orm_model import NaiveOrmModel


class GroupMembershipKindInfo(NaiveOrmModel):
    name: str


class GroupMembersInfoOut(NaiveOrmModel):
    id: int
    individual: IndividualInfoOut
    kind: List[
        GroupMembershipKindInfo
    ]  # TODO: Would be nicer to have it as a list of str


class GroupMembersInfoIn(NaiveOrmModel):
    individual: IndividualInfoIn
    kind: List[
        GroupMembershipKindInfo
    ]  # TODO: Would be nicer to have it as a list of str
