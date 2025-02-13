from datetime import datetime

from .individual import IndividualInfoRequest, IndividualInfoResponse
from .naive_orm_model import NaiveOrmModel


class GroupMembershipKindInfo(NaiveOrmModel):
    name: str | None


class GroupMembersInfoResponse(NaiveOrmModel):
    id: int
    individual: IndividualInfoResponse | None = []
    kind: list[GroupMembershipKindInfo] | None = None  # TODO: Would be nicer to have it as a list of str
    create_date: datetime = None
    write_date: datetime = None


class GroupMembersInfoRequest(IndividualInfoRequest):
    kind: list[GroupMembershipKindInfo] = None  # TODO: Would be nicer to have it as a list of str
