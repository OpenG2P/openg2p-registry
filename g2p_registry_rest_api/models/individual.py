from datetime import date

from pydantic import validator

from odoo.http import request

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
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
    birthdate: date = None
    birth_place: str = None
    is_group = False

    @validator("given_name")
    def validate_given_name(cls, v):  # noqa: B902
        if v is None or v.strip() == "":
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_002.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_002.get_error_code(),
                error_description="Given name is mandatory",
            )
        return v

    @validator("family_name")
    def validate_family_name(cls, v):  # noqa: B902
        if v is None or v.strip() == "":
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_002.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_002.get_error_code(),
                error_description="Family name is mandatory",
            )
        return v

    @validator("gender")
    def validate_gender(cls, value):  # noqa: B902
        options = request.env["gender.type"].search([("active", "=", True)])
        if value and not options.search([("code", "=", value)]):
            raise G2PApiValidationError(
                error_message=G2PErrorCodes.G2P_REQ_008.get_error_message(),
                error_code=G2PErrorCodes.G2P_REQ_008.get_error_code(),
                error_description=f"Invalid gender-{value}. It should be {[option.code for option in options]}",
            )
        return value
