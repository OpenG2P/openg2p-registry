from pydantic import BaseModel


class G2PErrorResponse(BaseModel):
    errorCode: str
    errorMessage: str
    errorDescription: str | None
