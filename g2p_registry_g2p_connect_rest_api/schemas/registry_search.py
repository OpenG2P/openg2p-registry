from pydantic import BaseModel

from .header import HeaderRequest, HeaderResponse
from .message import MessageRequest, MessageResponse


class RegistrySearchRequest(BaseModel):
    signature: str | None = None
    header: HeaderRequest
    message: MessageRequest


class RegistrySearchResponse(BaseModel):
    signature: str | None = ""
    header: HeaderResponse
    message: MessageResponse
