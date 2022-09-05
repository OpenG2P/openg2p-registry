from .registrant import RegistrantInfoIn, RegistrantInfoOut


class IndividualInfoOut(RegistrantInfoOut):
    is_group = False


class IndividualInfoIn(RegistrantInfoIn):
    is_group = False
