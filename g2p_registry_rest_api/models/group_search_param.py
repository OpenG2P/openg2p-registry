from extendable_pydantic import ExtendableModelMeta
from pydantic import BaseModel


class GroupSearchParam(BaseModel, metaclass=ExtendableModelMeta):

    id: int = None
    name: str = None
    include_members_full: bool = False
