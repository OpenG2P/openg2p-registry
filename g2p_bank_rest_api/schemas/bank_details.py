from odoo.addons.g2p_registry_rest_api.schemas import naive_orm_model


class BankDetailsRequest(naive_orm_model.NaiveOrmModel):
    bank_name: str = None
    acc_number: str = None


class BankDetailsResponse(naive_orm_model.NaiveOrmModel):
    bank_name: str = None
    acc_number: str = None
