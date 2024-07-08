from odoo.addons.g2p_registry_rest_api.schemas import registrant

from . import bank_details


class RegistrantAddlInfoRequest(registrant.RegistrantInfoRequest, extends=registrant.RegistrantInfoRequest):
    bank_ids: list[bank_details.BankDetailsRequest] | None = None


class RegistrantAddlInfoResponse(
    registrant.RegistrantInfoResponse, extends=registrant.RegistrantInfoResponse
):
    bank_ids: list[bank_details.BankDetailsResponse] | None = None
