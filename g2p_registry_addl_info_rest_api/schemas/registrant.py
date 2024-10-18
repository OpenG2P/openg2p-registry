from odoo.addons.g2p_registry_rest_api.schemas.registrant import RegistrantInfoRequest, RegistrantInfoResponse


class RegistrantAddlInfoIn(RegistrantInfoRequest, extends=RegistrantInfoRequest):
    additional_g2p_info: dict | list | None = None


class RegistrantAddlInfoOut(RegistrantInfoResponse, extends=RegistrantInfoResponse):
    additional_g2p_info: dict | list | None = None
