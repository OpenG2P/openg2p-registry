from typing import List, Optional

from odoo.addons.g2p_registry_rest_api.models import registrant

from . import bank_details


class RegistrantAddlInfoIn(
    registrant.RegistrantInfoIn, extends=registrant.RegistrantInfoIn
):
    bank_ids: Optional[List[bank_details.BankDetailsIn]]


class RegistrantAddlInfoOut(
    registrant.RegistrantInfoOut, extends=registrant.RegistrantInfoOut
):
    bank_ids: Optional[List[bank_details.BankDetailsOut]]
