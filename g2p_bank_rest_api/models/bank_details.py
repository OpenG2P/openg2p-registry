from odoo.addons.g2p_registry_rest_api.models import naive_orm_model


class BankDetailsIn(naive_orm_model.NaiveOrmModel):
    bank_name: str = None
    acc_number: str = None


class BankDetailsOut(naive_orm_model.NaiveOrmModel):
    bank_name: str = None
    acc_number: str = None
