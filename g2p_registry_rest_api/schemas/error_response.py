from .naive_orm_model import NaiveOrmModel


class G2PErrorResponse(NaiveOrmModel):
    errorCode: str
    errorMessage: str
    errorDescription: str | None
