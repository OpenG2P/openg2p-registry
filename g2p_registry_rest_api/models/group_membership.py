from typing import List

from .individual import IndividualInfo
from .naive_orm_model import NaiveOrmModel


class GroupMembershipKindInfo(NaiveOrmModel):
    name: str


class GroupMembersInfo(NaiveOrmModel):
    id: int
    individual: IndividualInfo
    kind: List[
        GroupMembershipKindInfo
    ]  # TODO: Would be nicer to have it as a list of str
