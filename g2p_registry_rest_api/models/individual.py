from datetime import date
from typing import List

import pydantic

from .registrant import Relationship2Out  # fmt: skip
from .registrant import (
    RegistrantInfoIn,
    RegistrantInfoOut,
    Relationship1In,
    Relationship1Out,
    Relationship2In,
)


class IndividualInfoOut(RegistrantInfoOut):
    given_name: str = None
    family_name: str = None
    gender: str = None
    birthdate: date = None
    age: str
    birth_place: str = None
    is_group = False
    relationships_1: List[Relationship1Out] = pydantic.Field(..., alias="related_1_ids")
    relationships_2: List[Relationship2Out] = pydantic.Field(..., alias="related_2_ids")


class IndividualInfoIn(RegistrantInfoIn):
    given_name: str = None
    family_name: str = None
    gender: str = None
    birthdate: date = None
    birth_place: str = None
    is_group = False
    relationships_1: List[Relationship1In] = None
    relationships_2: List[Relationship2In] = None
