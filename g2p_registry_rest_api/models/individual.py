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
    is_group = False
    relationships_1: List[Relationship1Out] = pydantic.Field(..., alias="related_1_ids")
    relationships_2: List[Relationship2Out] = pydantic.Field(..., alias="related_2_ids")


class IndividualInfoIn(RegistrantInfoIn):
    is_group = False
    relationships_1: List[Relationship1In]
    relationships_2: List[Relationship2In]
