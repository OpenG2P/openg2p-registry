from extendable_pydantic import ExtendableModelMeta
from pydantic import BaseModel


class IndividualSearchParam(BaseModel, metaclass=ExtendableModelMeta):
    id: int = None
    name: str = None
