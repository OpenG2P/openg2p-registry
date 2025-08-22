from odoo.addons.g2p_registry_rest_api.schemas.individual import (
    IndividualInfoRequest,
    IndividualInfoResponse,
    UpdateIndividualInfoRequest,
    UpdateIndividualInfoResponse,
)


class SocialRegistryDemoIndividualInfoResponse(IndividualInfoResponse, extends=IndividualInfoResponse):
    education_level: str | None = None
    employment_status: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    income: float | None = None


class SocialRegistryDemoIndividualInfoRequest(IndividualInfoRequest, extends=IndividualInfoRequest):
    education_level: str | None = None
    employment_status: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    income: float | None = None


class SocialRegistryDemoUpdateIndividualInfoRequest(
    UpdateIndividualInfoRequest, extends=UpdateIndividualInfoRequest
):
    education_level: str | None = None
    employment_status: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    income: float | None = None


class SocialRegistryDemoUpdateIndividualInfoResponse(
    UpdateIndividualInfoResponse, extends=UpdateIndividualInfoResponse
):
    education_level: str | None = None
    employment_status: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    income: float | None = None
