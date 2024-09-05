from datetime import datetime
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("-at_install", "post_install")
class TestVCIAPITestCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.fastapi_endpoint = self.env.ref("g2p_openid_vci_rest_api.fastapi_endpoint_vci")

    def mock_issue_vc(self):
        return {
            "credential": {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    "http://openg2p.local/api/v1/vci/.well-known/contexts.json",
                ],
                "id": "1234",
                "type": ["VerifiableCredential", "OpenG2PTestVerifiableCredential"],
                "issuer": "did:example:test12345678abcdefgh",
                "issuanceDate": f'{datetime.utcnow().isoformat(timespec = "milliseconds")}Z',
                "credentialSubject": {
                    "vcVer": "VC-V1",
                    "id": "http://openg2p.local/individual/1",
                    "fullName": [{"language": "eng", "value": "Full Name"}],
                },
            },
            "format": "ldp_vc",
            "acceptance_token": None,
            "c_nonce": None,
            "c_nonce_expires_in": None,
        }

    def mock_get_issuer_metadata(self):
        return {
            "credential_issuer": "http://openg2p.local",
            "credential_endpoint": "http://openg2p.local/api/v1/vci/credential",
            "credentials_supported": [
                {
                    "id": "OpenG2PTestVerifiableCredential",
                    "format": "ldp_vc",
                    "scope": "openg2p_registry_vc_ldp",
                    "cryptographic_binding_methods_supported": ["did:jwk"],
                    "credential_signing_alg_values_supported": ["RS256"],
                    "proof_types_supported": ["jwt"],
                    "credential_definition": {
                        "type": ["VerifiableCredential", "OpenG2PTestVerifiableCredential"],
                        "credentialSubject": {
                            "fullName": {"display": [{"name": "Name", "locale": "en"}]},
                        },
                    },
                    "display": [
                        {
                            "name": "OpenG2P Registry Credential",
                            "locale": "en",
                            "logo": {
                                "url": "http://openg2p.local/g2p_openid_vci/static/description/icon.png",
                                "alt_text": "a square logo of a OpenG2P",
                            },
                            "background_color": "#12107c",
                            "text_color": "#FFFFFF",
                        }
                    ],
                    "order": ["fullName"],
                }
            ],
        }

    def mock_get_contexts(self):
        return {
            "@context": {
                "OpenG2PTestVerifiableCredential": {
                    "@id": "https://openg2p.org/credential#OpenG2PTestVerifiableCredential",
                    "@context": [
                        "https://www.w3.org/2018/credentials/v1",
                        {
                            "@vocab": "https://openg2p.org/credential#OpenG2PTestVerifiableCredential#",
                            "credentialSubject": {
                                "@id": "credentialSubject",
                                "@type": "@id",
                                "@context": {
                                    "@vocab": (
                                        "https://openg2p.org/credential#"
                                        "OpenG2PTestVerifiableCredential#"
                                        "credentialSubject#"
                                    ),
                                    "fullName": {
                                        "@id": "fullName",
                                        "@type": "@id",
                                        "@context": {
                                            "value": "@value",
                                            "language": "@language",
                                        },
                                    },
                                },
                            },
                        },
                    ],
                }
            }
        }

    def mock_raise_error(self):
        raise ValueError("Temporary mock error")

    @patch("odoo.addons.g2p_openid_vci.models.vci_issuer.OpenIDVCIssuer.get_all_contexts_json")
    @patch("odoo.addons.g2p_openid_vci.models.vci_issuer.OpenIDVCIssuer.get_issuer_metadata_by_name")
    @patch("odoo.addons.g2p_openid_vci.models.vci_issuer.OpenIDVCIssuer.issue_vc")
    def test_vci_apis(self, mock_issue_vc, mock_issuer_metadata, mock_contexts):
        mock_issue_vc.side_effect = lambda *a, **kw: self.mock_issue_vc()
        mock_issuer_metadata.side_effect = lambda *a, **kw: self.mock_get_issuer_metadata()
        mock_contexts.side_effect = lambda *a, **kw: self.mock_get_contexts()

        res = self.url_open(
            "/api/v1/vci/credential",
            data='{"format":"ldp_vc", "credential_definition":{"type":[]}}',
            headers={"content-type": "application/json"},
        )
        self.assertEqual(401, res.status_code)

        res = self.url_open(
            "/api/v1/vci/credential",
            data='{"format":"ldp_vc", "credential_definition":{"type":[]}}',
            headers={"authorization": "Bearer token", "content-type": "application/json"},
        )
        self.assertEqual("Full Name", res.json()["credential"]["credentialSubject"]["fullName"][0]["value"])
        res = self.url_open("/api/v1/vci/.well-known/openid-credential-issuer")
        self.assertEqual(
            "OpenG2PTestVerifiableCredential",
            res.json()["credentials_supported"][0]["credential_definition"]["type"][1],
        )
        res = self.url_open("/api/v1/vci/.well-known/contexts.json")
        self.assertEqual(
            "@value",
            res.json()["@context"]["OpenG2PTestVerifiableCredential"]["@context"][1]["credentialSubject"][
                "@context"
            ]["fullName"]["@context"]["value"],
        )

        mock_issue_vc.side_effect = lambda *a, **kw: self.mock_raise_error()
        res = self.url_open(
            "/api/v1/vci/credential",
            data='{"format":"ldp_vc", "credential_definition":{"type":[]}}',
            headers={"authorization": "Bearer token", "content-type": "application/json"},
        )
        self.assertEqual("invalid_credential_request", res.json()["error"])
        self.assertTrue("Temporary mock error" in res.json()["error_description"])

    def test_misc(self):
        self.fastapi_endpoint.demo_auth_method = "http_basic"
        self.fastapi_endpoint.app = "demo"
        self.fastapi_endpoint._get_fastapi_routers()
