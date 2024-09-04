from extendable_pydantic import ExtendableModelMeta
from pydantic import BaseModel, ConfigDict


class VCIBaseModel(BaseModel, metaclass=ExtendableModelMeta):
    model_config = ConfigDict(extra="allow")


class CredetialRequestProof(VCIBaseModel):
    proof_type: str
    jwt: str | None = None
    cwt: str | None = None


class CredentialRequestDefintion(VCIBaseModel):
    type: list[str]


class CredentialRequest(VCIBaseModel):
    format: str
    proof: CredetialRequestProof | None = None
    credential_definition: CredentialRequestDefintion


class CredentialBaseResponse(VCIBaseModel):
    c_nonce: str | None = None
    c_nonce_expires_in: int | None = None


class CredentialResponse(CredentialBaseResponse):
    format: str
    credential: dict
    acceptance_token: str | None = None


class CredentialErrorResponse(CredentialBaseResponse):
    error: str
    error_description: str


class CredentialIssuerDisplayLogoResponse(VCIBaseModel):
    url: str
    alt_text: str


class CredentialIssuerDisplayResponse(VCIBaseModel):
    name: str
    locale: str
    logo: CredentialIssuerDisplayLogoResponse
    background_color: str
    text_color: str


class CredentialIssuerConfigResponse(VCIBaseModel):
    id: str | None = None
    format: str
    scope: str
    cryptographic_binding_methods_supported: list[str]
    credential_signing_alg_values_supported: list[str]
    credential_definition: dict
    proof_types_supported: dict | list
    display: list[CredentialIssuerDisplayResponse]


class CredentialIssuerResponse(VCIBaseModel):
    credential_issuer: str
    credential_endpoint: str
    credentials_supported: list[CredentialIssuerConfigResponse] | None = None
    credential_configurations_supported: dict[str, CredentialIssuerConfigResponse] | None = None
