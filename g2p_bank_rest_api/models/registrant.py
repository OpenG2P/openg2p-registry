from odoo.addons.g2p_registry_rest_api.models import registrant

from . import bank_details


class RegistrantAddlInfoIn(registrant.RegistrantInfoIn, extends=registrant.RegistrantInfoIn):
    bank_ids: list[bank_details.BankDetailsIn] | None


class RegistrantAddlInfoOut(registrant.RegistrantInfoOut, extends=registrant.RegistrantInfoOut):
    bank_ids: list[bank_details.BankDetailsOut] | None
