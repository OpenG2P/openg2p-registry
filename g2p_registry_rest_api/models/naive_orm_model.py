# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from extendable_pydantic import ExtendableModelMeta
from pydantic import BaseModel

from odoo.addons.pydantic import utils


class NaiveOrmModel(BaseModel, metaclass=ExtendableModelMeta):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
