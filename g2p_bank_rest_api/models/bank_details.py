from pydantic import validator

from odoo.http import request

from odoo.addons.g2p_registry_rest_api.exceptions import base_exception, error_codes
from odoo.addons.g2p_registry_rest_api.models import naive_orm_model


class BankDetailsIn(naive_orm_model.NaiveOrmModel):
    bank_name: str = None
    acc_number: str = None

    @validator("acc_number")
    def validate_acc_number_duplicate(cls, value):  # noqa: B902
        if value:
            acc_num = request.env["res.partner.bank"].search([("acc_number", "=", value)])
            if acc_num:
                raise base_exception.G2PApiValidationError(
                    error_message=error_codes.G2PErrorCodes.G2P_REQ_009.get_error_message(),
                    error_code=error_codes.G2PErrorCodes.G2P_REQ_009.get_error_code(),
                    error_description="Account number - %s cannot be duplicate." % value,
                )
        return value


class BankDetailsOut(naive_orm_model.NaiveOrmModel):
    bank_name: str = None
    acc_number: str = None
