import json
import logging
import os
import uuid
from datetime import datetime

import jq
import requests
from cryptography.hazmat.primitives import hashes
from jose import jwt
from pyld import jsonld

from odoo import api, fields, models, tools
from odoo.tools import misc

from ..json_encoder import VCJSONEncoder

_logger = logging.getLogger(__name__)


class OpenIDVCIssuer(models.Model):
    _name = "g2p.openid.vci.issuers"
    _description = "OpenID VCI Issuer"

    name = fields.Char(required=True)
    issuer_type = fields.Selection(
        [
            (
                "Registry",
                "Registry",
            )
        ],
        required=True,
    )
    scope = fields.Char(required=True)
    supported_format = fields.Selection([("ldp_vc", "ldp_vc")], default="ldp_vc", required=True)
    unique_issuer_id = fields.Char("Unique Issuer ID", default="did:example:12345678abcdefgh")

    encryption_provider_id = fields.Many2one("g2p.encryption.provider")

    auth_sub_id_type_id = fields.Many2one("g2p.id.type", "Auth Subject ID Type")

    auth_allowed_auds = fields.Text("Auth Allowed Audiences")
    auth_allowed_issuers = fields.Text()
    auth_issuer_jwks_mapping = fields.Text()
    auth_allowed_client_ids = fields.Text("Auth Allowed Client IDs")

    # These fields cannot be empty. They will get autofilled based on issuer_type
    credential_type = fields.Char()
    credential_format = fields.Text()
    issuer_metadata_text = fields.Text()
    contexts_json = fields.Text()

    @api.model
    def issue_vc(self, credential_request: dict, token: str):
        # TODO: Raise better errors and error types
        auth_claims_unverified = jwt.get_unverified_claims(token)
        auth_scopes = auth_claims_unverified.get("scope", "").split()
        auth_aud = auth_claims_unverified.get("aud", "")
        if isinstance(auth_aud, str):
            auth_aud = auth_aud.split()

        request_format = credential_request["format"]
        request_types = credential_request["credential_definition"]["type"]

        if not auth_scopes:
            raise ValueError("Scope not found in auth token.")

        search_domain = [
            ("supported_format", "=", request_format),
            ("scope", "in", auth_scopes),
        ]
        if request_types:
            search_domain.append(("credential_type", "in", request_types))
        credential_issuer = self.sudo().search(search_domain)
        if credential_issuer and len(credential_issuer):
            credential_issuer = credential_issuer[0]
        else:
            raise ValueError("Invalid combination of scope, credential type, format")

        request_auth_iss = auth_claims_unverified["iss"]
        # TODO: Client id validation

        try:
            auth_allowed_iss = (credential_issuer.auth_allowed_issuers or "").split()
            auth_allowed_aud = (credential_issuer.auth_allowed_auds or "").split()
            auth_jwks_mapping = (credential_issuer.auth_issuer_jwks_mapping or "").split()
            # TODO: Cache JWKS somehow
            jwks = credential_issuer.get_auth_jwks(
                request_auth_iss,
                auth_allowed_iss,
                auth_jwks_mapping,
            )
            jwt.decode(
                token,
                jwks,
                issuer=auth_allowed_iss,
                options={"verify_aud": False},
            )
            if auth_allowed_aud and not set(auth_allowed_aud).issubset(set(auth_aud)):
                raise ValueError("Invalid Audience")
        except Exception as e:
            if isinstance(e, ValueError) and "Invalid Audience" in str(e):
                raise e
            raise ValueError("Invalid Auth Token received") from e

        issue_vc_func = getattr(credential_issuer, f"issue_vc_{credential_issuer.issuer_type}")

        cred_res = issue_vc_func(
            auth_claims=auth_claims_unverified,
            credential_request=credential_request,
        )
        _logger.debug("Credential Response for DEBUG; %s", json.dumps(cred_res))
        return cred_res

    def issue_vc_Registry(self, auth_claims, credential_request):
        self.ensure_one()
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
        reg_id = (
            self.env["g2p.reg.id"]
            .sudo()
            .search(
                [
                    ("id_type", "=", self.auth_sub_id_type_id.id),
                    ("value", "=", auth_claims["sub"]),
                ],
                limit=1,
            )
        )
        partner = None
        if not reg_id:
            raise ValueError("ID not found in DB. Invalid Subject Received in auth claims")

        partner = reg_id.partner_id

        partner_dict = partner.read()[0]
        reg_ids_dict = {reg_id.id_type.name: reg_id.read()[0] for reg_id in partner.reg_ids}

        curr_datetime = f'{datetime.utcnow().isoformat(timespec = "milliseconds")}Z'
        credential = jq.first(
            self.credential_format,
            VCJSONEncoder.python_dict_to_json_dict(
                {
                    "vc_id": str(uuid.uuid4()),
                    "web_base_url": web_base_url,
                    "issuer": self.read()[0],
                    "curr_datetime": curr_datetime,
                    "partner": partner_dict,
                    "partner_address": self.get_full_address(partner.address),
                    "partner_face": self.get_image_base64_data_in_url((partner.image_1920 or b"").decode()),
                    "reg_ids": reg_ids_dict,
                },
            ),
        )
        credential_response = {
            "credential": self.sign_and_issue_credential(credential),
            "format": credential_request["format"],
        }
        return credential_response

    def sign_and_issue_credential(self, credential: dict) -> dict:
        self.ensure_one()

        ld_proof = self.build_empty_ld_proof()
        normalised_ld_prood_str = jsonld.normalize(
            ld_proof, {"algorithm": "URDNA2015", "format": "application/n-quads"}
        )
        normalized_json_ld_str = jsonld.normalize(
            credential, {"algorithm": "URDNA2015", "format": "application/n-quads"}
        )

        signature = self.get_encryption_provider().jwt_sign(
            self.sha256_digest(normalised_ld_prood_str.encode())
            + self.sha256_digest(normalized_json_ld_str.encode()),
            include_payload=False,
            include_certificate=True,
            include_cert_hash=True,
        )
        ld_proof["jws"] = signature
        ret = dict(credential)
        ret["proof"] = ld_proof
        return ret

    def build_empty_ld_proof(self):
        self.ensure_one()
        curr_datetime = f'{datetime.utcnow().isoformat(timespec = "milliseconds")}Z'
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
        # TODO: Remove this hardcoding
        return {
            "@context": [
                "https://w3id.org/security/v2",
            ],
            "type": "RsaSignature2018",
            "created": curr_datetime,
            "verificationMethod": f"{web_base_url}/api/v1/security/.well-known/jwks.json",
            "proofPurpose": "assertionMethod",
        }

    @api.model
    def get_issuer_metadata_by_name(self, issuer_name=""):
        """
        If issuer_name param is null, this returns all issuer's metdata.
        """
        search_domain = []
        if issuer_name:
            search_domain.append(("name", "=", issuer_name))
        vci_issuers = self.sudo().search(search_domain)
        return vci_issuers.get_issuer_metadata()

    def get_issuer_metadata(self):
        vci_issuers = self.read()
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
        cred_configs = None
        for issuer in vci_issuers:
            issuer["web_base_url"] = web_base_url
            issuer_metadata = jq.first(
                issuer["issuer_metadata_text"], VCJSONEncoder.python_dict_to_json_dict(issuer)
            )
            if isinstance(issuer_metadata, list):
                if not cred_configs:
                    cred_configs = []
                cred_configs.extend(issuer_metadata)
            elif isinstance(issuer_metadata, dict):
                if not cred_configs:
                    cred_configs = {}
                cred_configs.update(issuer_metadata)
        response = {
            "credential_issuer": web_base_url,
            "credential_endpoint": f"{web_base_url}/api/v1/vci/credential",
        }
        if isinstance(cred_configs, list):
            response["credentials_supported"] = cred_configs
        elif isinstance(cred_configs, dict):
            response["credential_configurations_supported"] = cred_configs
        return response

    @api.model
    def get_all_contexts_json(self):
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
        context_jsons = self.sudo().search([]).read(["contexts_json"])
        final_context = {"@context": {}}
        for context in context_jsons:
            context = context["contexts_json"].strip()
            if context:
                final_context["@context"].update(
                    json.loads(context.replace("web_base_url", web_base_url))["@context"]
                )
        return final_context

    def get_auth_jwks(
        self,
        auth_issuer: str,
        auth_allowed_issuers: list[str],
        auth_allowed_jwks_urls: list[str],
    ):
        self.ensure_one()
        jwk_url = None
        try:
            jwk_url = auth_allowed_jwks_urls[auth_allowed_issuers.index(auth_issuer)]
        except Exception:
            jwk_url = f'{auth_issuer.rstrip("/")}/.well-known/jwks.json'
        return requests.get(jwk_url, timeout=20).json()

    def get_encryption_provider(self):
        self.ensure_one()
        prov = self.encryption_provider_id
        if not prov:
            prov = self.env.ref("g2p_encryption.encryption_provider_default")
        return prov

    @api.model
    def get_full_address(self, address: str) -> dict:
        try:
            return json.loads(address)
        except Exception:
            return {"street_address": address}

    @api.model
    def get_image_base64_data_in_url(self, image_base64: str) -> str:
        if not image_base64:
            return None
        image = tools.base64_to_image(image_base64)
        return f"data:image/{image.format.lower()};base64,{image_base64}"

    @api.model
    def sha256_digest(self, data: bytes) -> bytes:
        sha = hashes.Hash(hashes.SHA256())
        sha.update(data)
        return sha.finalize()[0:32]

    @api.constrains("credential_type", "issuer_type")
    def onchange_credential_type(self):
        for rec in self:
            if not rec.credential_type:
                getattr(rec, f"set_default_credential_type_{rec.issuer_type}")()

    @api.constrains("credential_format", "issuer_type")
    def onchange_credential_format(self):
        for rec in self:
            if not rec.credential_format:
                getattr(rec, f"set_from_static_file_{rec.issuer_type}")(
                    file_name="default_credential_format.jq",
                    field_name="credential_format",
                )

    @api.constrains("issuer_metadata_text", "issuer_type")
    def onchange_issuer_metadata_text(self):
        for rec in self:
            if not rec.issuer_metadata_text:
                getattr(rec, f"set_from_static_file_{rec.issuer_type}")(
                    file_name="default_issuer_metadata.jq",
                    field_name="issuer_metadata_text",
                )

    @api.constrains("contexts_json", "issuer_type")
    def onchange_contexts_json(self):
        for rec in self:
            if not rec.contexts_json:
                getattr(rec, f"set_from_static_file_{rec.issuer_type}")(
                    file_name="default_contexts.json",
                    field_name="contexts_json",
                )

    def set_default_credential_type_Registry(self):
        self.credential_type = "OpenG2PRegistryVerifiableCredential"

    def set_from_static_file_Registry(
        self, module_name="g2p_openid_vci", file_name="", field_name="", **kwargs
    ):
        text = ""
        try:
            with misc.file_open(os.path.join(module_name, "data", file_name)) as file:
                text = file.read()
                if field_name:
                    self.write({field_name: text})
        except Exception:
            _logger.exception(f"Could not set default {field_name}")
        return text

    # TODO: Verify proof and do wallet binding
    # @api.model
    # def verify_proof_and_bind(self, credential_request):
    #     request_proof_type = credential_request["proof"]["proof_type"]
    #     request_proof_jwt = credential_request["proof"]["jwt"]
    #     request_proof = None
    #     if request_proof_type and request_proof_jwt and request_proof_type == "jwt":
    #         request_proof = jwt.get_unverified_claims(request_proof_jwt)
    #     else:
    #         raise ValueError("Only JWT proof supported")
