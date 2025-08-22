from datetime import datetime

from pydantic import BaseModel

from .status_codes import StatusEnum


class HeaderRequest(BaseModel):
    version: str = "1.0.0"
    message_id: str = ""
    message_ts: datetime = datetime.now()
    action: str = "search"
    sender_id: str = ""
    sender_uri: str | None = ""
    receiver_id: str | None = ""
    total_count: int
    is_msg_encrypted: bool = False
    meta: dict = {}


class HeaderResponse(BaseModel):
    version: str = "1.0.0"
    message_id: str | None = ""
    message_ts: datetime = datetime.now()
    action: str = "on-search"
    status: StatusEnum
    status_reason_code: str = ""
    status_reason_message: str | None = ""
    total_count: int | None = 0
    completed_count: int | None = 0
    sender_id: str | None = ""
    receiver_id: str | None = ""
    is_msg_encrypted: bool = False
    meta: dict | None = {}
