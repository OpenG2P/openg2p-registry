from extendable_pydantic import ExtendableModelMeta
from pydantic import BaseModel, ConfigDict


class NaiveOrmModel(BaseModel, metaclass=ExtendableModelMeta):
    model_config = ConfigDict(from_attributes=True)
