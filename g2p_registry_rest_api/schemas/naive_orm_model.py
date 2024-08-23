from typing import Any

from extendable_pydantic import ExtendableModelMeta
from pydantic import BaseModel, ConfigDict, model_validator

from odoo import fields, models


class NaiveOrmModel(BaseModel, metaclass=ExtendableModelMeta):
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def parse_odoo_obj(cls, obj: Any) -> Any:
        if isinstance(obj, models.BaseModel):
            output_obj = {}
            for key in cls.model_fields.keys():
                if key in obj._fields:
                    res = getattr(obj, key)
                    field = obj._fields[key]
                    if res is False and field.type != "boolean":
                        res = None
                    if field.type == "date" and not res:
                        res = None
                    if field.type == "datetime":
                        if not res:
                            res = None
                        # Get the timestamp converted to the client's timezone.
                        # This call also add the tzinfo into the datetime object
                        res = fields.Datetime.context_timestamp(obj, res)
                    if field.type == "many2one" and not res:
                        res = None
                    if field.type in ["one2many", "many2many"]:
                        res = list(res)

                    output_obj[key] = res

            return output_obj
        return obj
