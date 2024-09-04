# pylint: disable=[W7936]

import base64
import json
import logging
import os
import secrets
from datetime import datetime

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding
from jose import jwt
from jwcrypto import jwk

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

KEYMANAGER_API_BASE_URL = os.getenv("KEYMANAGER_API_BASE_URL", "http://keymanager.keymanager/v1/keymanager")
KEYMANAGER_AUTH_URL = os.getenv(
    "KEYMANAGER_AUTH_URL",
    "http://keycloak.keycloak/realms/openg2p/protocol/openid-connect/token",
)
KEYMANAGER_AUTH_CLIENT_ID = os.getenv("KEYMANAGER_AUTH_CLIENT_ID", "openg2p-admin-client")
KEYMANAGER_AUTH_CLIENT_SECRET = os.getenv("KEYMANAGER_AUTH_CLIENT_SECRET", "")
KEYMANAGER_AUTH_GRANT_TYPE = os.getenv("KEYMANAGER_AUTH_GRANT_TYPE", "client_credentials")


class KeymanagerEncryptionProvider(models.Model):
    _inherit = "g2p.encryption.provider"

    type = fields.Selection(selection_add=[("keymanager", "Keymanager")])

    @api.model
    def _km_random_secret(self):
        return secrets.token_urlsafe()

    @api.model
    def km_generate_current_time(self):
        return f'{datetime.utcnow().isoformat(timespec = "milliseconds")}Z'

    keymanager_api_base_url = fields.Char("Keymanager API Base URL", default=KEYMANAGER_API_BASE_URL)
    keymanager_api_timeout = fields.Integer("Keymanager API Timeout", default=10)
    keymanager_auth_url = fields.Char("Keymanager Auth URL", default=KEYMANAGER_AUTH_URL)
    keymanager_auth_client_id = fields.Char("Keymanager Auth Client ID", default=KEYMANAGER_AUTH_CLIENT_ID)
    keymanager_auth_client_secret = fields.Char(default=KEYMANAGER_AUTH_CLIENT_SECRET)
    keymanager_auth_grant_type = fields.Char(default=KEYMANAGER_AUTH_GRANT_TYPE)

    keymanager_access_token = fields.Char()
    keymanager_access_token_expiry = fields.Datetime()

    keymanager_encrypt_application_id = fields.Char(
        "Keymanager Encrypt Application ID", default="REGISTRATION"
    )
    keymanager_encrypt_reference_id = fields.Char("Keymanager Encrypt Reference ID", default="ENCRYPT")

    keymanager_sign_application_id = fields.Char("Keymanager Sign Application ID", default="ID_REPO")
    keymanager_sign_reference_id = fields.Char("Keymanager Sign Reference ID", default="")

    keymanager_encrypt_salt = fields.Char(default=_km_random_secret)
    keymanager_encrypt_aad = fields.Char(default=_km_random_secret)

    def encrypt_data_keymanager(self, data: bytes, **kwargs) -> bytes:
        self.ensure_one()
        access_token = self.km_get_access_token()
        current_time = self.km_generate_current_time()
        url = f"{self.keymanager_api_base_url}/encrypt"
        headers = {"Cookie": f"Authorization={access_token}"}
        payload = {
            "id": "string",
            "version": "string",
            "requesttime": current_time,
            "metadata": {},
            "request": {
                "applicationId": self.keymanager_encrypt_application_id or "",
                "referenceId": self.keymanager_encrypt_reference_id or "",
                "timeStamp": current_time,
                "data": self.km_urlsafe_b64encode(data),
                "salt": self.keymanager_encrypt_salt,
                "aad": self.keymanager_encrypt_aad,
            },
        }
        response = requests.post(url, json=payload, headers=headers, timeout=self.keymanager_api_timeout)
        _logger.debug("Keymanager Encrypt API response: %s", response.text)
        response.raise_for_status()
        if response:
            response = response.json()
        if response:
            response = response.get("response")
        if response:
            return self.km_urlsafe_b64decode(response.get("data"))
        raise ValueError("Could not encrypt data, invalid keymanager response")

    def decrypt_data_keymanager(self, data: bytes, **kwargs) -> bytes:
        self.ensure_one()
        access_token = self.km_get_access_token()
        current_time = self.km_generate_current_time()
        url = f"{self.keymanager_api_base_url}/decrypt"
        headers = {"Cookie": f"Authorization={access_token}"}
        payload = {
            "id": "string",
            "version": "string",
            "requesttime": current_time,
            "metadata": {},
            "request": {
                "applicationId": self.keymanager_encrypt_application_id or "",
                "referenceId": self.keymanager_encrypt_reference_id or "",
                "timeStamp": current_time,
                "data": self.km_urlsafe_b64encode(data),
                "salt": self.keymanager_encrypt_salt,
                "aad": self.keymanager_encrypt_aad,
            },
        }
        response = requests.post(url, json=payload, headers=headers, timeout=self.keymanager_api_timeout)
        _logger.debug("Keymanager Decrypt API response: %s", response.text)
        response.raise_for_status()
        if response:
            response = response.json()
        if response:
            response = response.get("response")
        if response:
            return self.km_urlsafe_b64decode(response.get("data"))
        raise ValueError("Could not decrypt data, invalid keymanager response")

    def jwt_sign_keymanager(
        self,
        data,
        include_payload=True,
        include_certificate=False,
        include_cert_hash=False,
        **kwargs,
    ) -> str:
        self.ensure_one()
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()

        access_token = self.km_get_access_token()
        current_time = self.km_generate_current_time()
        url = f"{self.keymanager_api_base_url}/jwtSign"
        headers = {"Cookie": f"Authorization={access_token}"}
        payload = {
            "id": "string",
            "version": "string",
            "requesttime": current_time,
            "metadata": {},
            "request": {
                "dataToSign": self.km_urlsafe_b64encode(data),
                "applicationId": self.keymanager_sign_application_id or "",
                "referenceId": self.keymanager_sign_reference_id or "",
                "includePayload": include_payload,
                "includeCertificate": include_certificate,
                "includeCertHash": include_cert_hash,
            },
        }
        response = requests.post(url, json=payload, headers=headers, timeout=self.keymanager_api_timeout)
        _logger.debug("Keymanager JWT Sign API response: %s", response.text)
        response.raise_for_status()
        if response:
            response = response.json()
        if response:
            response = response.get("response", {})
        if response:
            return response.get("jwtSignedData")
        raise ValueError("Could not sign jwt, invalid keymanager response")

    def jwt_verify_keymanager(self, data: str, **kwargs):
        self.ensure_one()
        access_token = self.km_get_access_token()
        current_time = self.km_generate_current_time()
        url = f"{self.keymanager_api_base_url}/jwtVerify"
        headers = {"Cookie": f"Authorization={access_token}"}
        payload = {
            "id": "string",
            "version": "string",
            "requesttime": current_time,
            "metadata": {},
            "request": {
                "jwtSignatureData": data,
                "applicationId": self.keymanager_sign_application_id or "",
                "referenceId": self.keymanager_sign_reference_id or "",
                "validateTrust": False,
            },
        }
        response = requests.post(url, json=payload, headers=headers, timeout=self.keymanager_api_timeout)
        _logger.debug("Keymanager JWT Verify API response: %s", response.text)
        response.raise_for_status()
        if response:
            response = response.json()
        if response:
            response = response.get("response", {})
        if response:
            response = response.get("signatureValid", False)
        else:
            raise ValueError("Could not verify jwt, invalid keymanager response")
        if response:
            return jwt.get_unverified_claims(data)
        raise ValueError("invalid jwt signature")

    def get_jwks_keymanager(self, **kwargs):
        # TODO: Cache this JWKS response somehow
        self.ensure_one()
        access_token = self.km_get_access_token()
        jwks = []
        for app_id, ref_id, use in (
            (
                self.keymanager_encrypt_application_id or "",
                self.keymanager_encrypt_reference_id or "",
                "enc",
            ),
            (
                self.keymanager_sign_application_id or "",
                self.keymanager_sign_reference_id or "",
                "sig",
            ),
        ):
            url = f"{self.keymanager_api_base_url}/getAllCertificates"
            if self.keymanager_sign_application_id:
                url += f"?applicationId={app_id}"
            if self.keymanager_sign_reference_id:
                url += f"&referenceId={ref_id}"
            headers = {"Cookie": f"Authorization={access_token}"}
            response = requests.get(url, headers=headers, timeout=self.keymanager_api_timeout)
            _logger.debug("Keymanager get Certificate API response: %s", response.text)
            response.raise_for_status()
            certs = response.json().get("response", {}).get("allCertificates", [])
            for cert in certs:
                jwks.append(
                    self.km_convert_x509_pem_to_jwk(
                        cert.get("certificateData", "").encode(),
                        use=use,
                        kid=cert.get("keyId"),
                    )
                )
        return {"keys": jwks}

    @api.model
    def km_convert_x509_pem_to_jwk(self, cert: bytes, use=None, kid=None):
        x509_cert = x509.load_pem_x509_certificate(cert)
        public_key = x509_cert.public_key()
        new = jwk.JWK()
        new.import_from_pyca(public_key)
        new.update(
            {
                "x5c": [base64.b64encode(x509_cert.public_bytes(Encoding.DER)).decode()],
                "x5t": self.km_urlsafe_b64encode(x509_cert.fingerprint(hashes.SHA1())),
                "x5t#S256": self.km_urlsafe_b64encode(x509_cert.fingerprint(hashes.SHA256())),
            }
        )
        if kid:
            new["kid"] = kid
        if use:
            new["use"] = use
        return dict(new)

    def km_get_access_token(self):
        self.ensure_one()
        if (
            self.keymanager_access_token
            and self.keymanager_access_token_expiry
            and self.keymanager_access_token_expiry > datetime.utcnow()
        ):
            return self.keymanager_access_token
        data = {
            "client_id": self.keymanager_auth_client_id,
            "client_secret": self.keymanager_auth_client_secret,
            "grant_type": self.keymanager_auth_grant_type,
        }
        response = requests.post(self.keymanager_auth_url, data=data, timeout=self.keymanager_api_timeout)
        _logger.debug("Keymanager get Certificates API response: %s", response.text)
        response.raise_for_status()
        access_token = response.json().get("access_token", None)
        token_exp = jwt.get_unverified_claims(access_token).get("exp")
        self.write(
            {
                "keymanager_access_token": access_token,
                "keymanager_access_token_expiry": datetime.fromtimestamp(token_exp)
                if isinstance(token_exp, int)
                else datetime.fromisoformat(token_exp)
                if isinstance(token_exp, str)
                else token_exp,
            }
        )
        return access_token

    @api.model
    def km_urlsafe_b64encode(self, input_data: bytes) -> str:
        return base64.urlsafe_b64encode(input_data).decode().rstrip("=")

    @api.model
    def km_urlsafe_b64decode(self, input_data: str) -> bytes:
        return base64.urlsafe_b64decode(input_data.encode() + b"=" * (-len(input_data) % 4))
