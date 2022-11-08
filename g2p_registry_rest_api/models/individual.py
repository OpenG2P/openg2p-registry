from datetime import date, datetime

import pydantic

from .registrant import RegistrantInfoIn, RegistrantInfoOut


class IndividualInfoOut(RegistrantInfoOut):
    given_name: str = None
    family_name: str = None
    gender: str = None
    birthdate: date = None
    age: str
    birth_place: str = None
    is_group = False


class IndividualInfoIn(RegistrantInfoIn):
    given_name: str = None
    family_name: str = None
    gender: str = None
    birthdate: date = None
    birth_place: str = None
    is_group = False

    @pydantic.validator("birthdate", pre=True)
    def birthdate_parse_validate(cls, value):  # noqa: B902
        try:
            return datetime.strptime(value, "%Y/%m/%d").date()
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%d").date()
