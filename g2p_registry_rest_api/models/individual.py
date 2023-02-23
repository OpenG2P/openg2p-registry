from datetime import date

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
    given_name: str = None
    addl_name: str = None
    family_name: str = None
    gender: str = None
    birthdate: date = None
    birth_place: str = None
    is_group = False
