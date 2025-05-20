import pydantic

from .group_membership import GroupMembersInfoRequest, GroupMembersInfoResponse
from .registrant import RegistrantInfoRequest, RegistrantInfoResponse


class GroupShortInfoOut(RegistrantInfoResponse):
    pass


class GroupInfoResponse(RegistrantInfoResponse):
    is_group: bool = True
    members: list[GroupMembersInfoResponse] = pydantic.Field([], alias="group_membership_ids")
    # kind: str | None = pydantic.Field(..., alias="kind_as_str")
    is_partial_group: bool


class GroupInfoRequest(RegistrantInfoRequest):
    is_group: bool = True
    members: list[GroupMembersInfoRequest] = []
    kind: str | None = None
    is_partial_group: bool | None = None
