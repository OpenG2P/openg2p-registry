from datetime import date

from pydantic import validator

from .registrant import RegistrantInfoIn, RegistrantInfoOut


class IndividualInfoOut(RegistrantInfoOut):
    given_name: str = None
    addl_name: str = None
    family_name: str = None
    gender: str = None
    birthdate: date = None
    age: str
    birth_place: str = None
    is_group = False


class IndividualInfoIn(RegistrantInfoIn):
    given_name: str
    addl_name: str = None
    family_name: str
    gender: str = None
    gender: str = None
    birthdate: date = None
    birth_place: str = None
    is_group = False

    @validator("given_name")
    def validate_given_name(cls, v):
        if v is None or v.strip() == "":
            raise ValueError("Given name is mandatory.")
        return v

    @validator("family_name")
    def validate_family_name(cls, v):
        if v is None or v.strip() == "":
            raise ValueError("Family name is mandatory.")
        return v
