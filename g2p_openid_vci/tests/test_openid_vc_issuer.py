import base64
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import requests
from jose import jws, jwt
from jwcrypto import jwk

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, _super_send
from odoo.tools import misc

from ..json_encoder import VCJSONEncoder


@tagged("-at_install", "post_install")
class TestVCIIssuerRegistry(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].set_param("web.base.url", "http://openg2p.local")
        self.id_type = self.env["g2p.id.type"].create(
            {
                "name": "NATIONAL ID",
            }
        )
        self.issuer_scope = "openg2p_registry_vc_ldp"
        self.issuer = self.env["g2p.openid.vci.issuers"].create(
            {
                "name": "Test Issuer",
                "issuer_type": "Registry",
                "scope": self.issuer_scope,
                "auth_sub_id_type_id": self.id_type.id,
                "auth_allowed_issuers": "http://openg2p.local/auth",
            }
        )
        self.issuer_2 = self.env["g2p.openid.vci.issuers"].create(
            {
                "name": "Test Issuer 2",
                "issuer_type": "Registry",
                "scope": "openg2p_registry_2_vc_ldp",
                "auth_sub_id_type_id": self.id_type.id,
                "auth_allowed_issuers": "http://openg2p.local/auth",
                "contexts_json": " ",
            }
        )
        self.jsonld_contexts = self.env["g2p.openid.vci.issuers"].get_all_contexts_json()

        self.registrant_national_id = "123456789"
        self.registrant_face_bytes = base64.b64encode(
            misc.file_open(os.path.join("base", "static", "img", "avatar.png"), mode="rb").read()
        )
        self.registrant = self.env["res.partner"].create(
            {
                "name": "Givenname Familyname",
                "image_1920": self.registrant_face_bytes,
                "reg_ids": [(0, 0, {"id_type": self.id_type.id, "value": self.registrant_national_id})],
            }
        )

        self.jwk = jwk.JWK.generate(kty="RSA", size=2048, alg="RS256", use="sig", kid="12345")
        self.public_jwks = {"keys": [self.jwk.export(private_key=False, as_dict=True)]}

        self.default_auth_jwt = jwt.encode(
            {
                "scope": self.issuer_scope,
                "iss": "http://openg2p.local/auth",
                "aud": "http://openg2p.local/api/v1/vci/credential",
                "sub": self.registrant_national_id,
                "exp": int(datetime.utcnow().timestamp()) + 5 * 60,
            },
            self.jwk,
            algorithm="RS256",
        )

    # TODO: This is only required because of external context url resolution
    @classmethod
    def _request_handler(cls, s: requests.Session, r: requests.PreparedRequest, /, **kw):
        return _super_send(s, r, **kw)

    def mock_request_get(self, url, **kwargs):
        if url == "http://openg2p.local/auth/.well-known/jwks.json":
            res = MagicMock()
            res.json.return_value = self.public_jwks
            res.headers = {}
            return res
        elif url == "http://openg2p.local/api/v1/vci/.well-known/contexts.json":
            res = MagicMock()
            res.json.return_value = self.jsonld_contexts
            res.headers = {}
            return res
        return requests.request("get", url, timeout=10, **kwargs)

    def mock_jwt_sign(self, data, **kwargs):
        return jws.sign(data, self.jwk, algorithm="RS256")

    @patch("requests.get")
    @patch("odoo.addons.g2p_encryption.models.encryption_provider.G2PEncryptionProvider.jwt_sign")
    def test_issue_vc_normal(self, mock_jwt_sign, mock_request):
        mock_request.side_effect = self.mock_request_get
        mock_jwt_sign.side_effect = self.mock_jwt_sign
        self.issuer.encryption_provider_id = self.env.ref("g2p_encryption.encryption_provider_default")
        res = self.env["g2p.openid.vci.issuers"].issue_vc(
            {"format": "ldp_vc", "credential_definition": {"type": []}}, self.default_auth_jwt
        )
        cred = res["credential"]
        cred_subject = cred["credentialSubject"]

        self.assertTrue("OpenG2PRegistryVerifiableCredential" in cred["type"])
        self.assertTrue("Givenname Familyname" in [name["value"] for name in cred_subject["name"]])
        self.assertTrue(not cred_subject["email"])
        self.assertTrue(not cred_subject["phone"])
        self.assertTrue(not cred_subject["addressLine1"])
        self.assertTrue(not cred_subject["postalCode"])
        self.assertEqual("123456789", cred_subject["UIN"])
        self.assertEqual(f"data:image/png;base64,{self.registrant_face_bytes.decode()}", cred_subject["face"])
        self.assertEqual("ldp_vc", res["format"])

    @patch("requests.get")
    @patch("odoo.addons.g2p_encryption.models.encryption_provider.G2PEncryptionProvider.jwt_sign")
    def test_issue_vc_normal_without_face(self, mock_jwt_sign, mock_request):
        mock_request.side_effect = self.mock_request_get
        mock_jwt_sign.side_effect = self.mock_jwt_sign
        self.registrant.image_1920 = None
        res = self.env["g2p.openid.vci.issuers"].issue_vc(
            {"format": "ldp_vc", "credential_definition": {"type": []}}, self.default_auth_jwt
        )
        cred_subject = res["credential"]["credentialSubject"]
        self.assertTrue(not cred_subject["face"])

    def test_issue_vc_unknown_type(self):
        with self.assertRaises(ValueError) as context:
            self.env["g2p.openid.vci.issuers"].issue_vc(
                {"format": "ldp_vc", "credential_definition": {"type": ["RandomVC"]}}, self.default_auth_jwt
            )
        self.assertTrue("Invalid combination of scope, credential type, format" in str(context.exception))

    def test_issue_vc_no_scope(self):
        with self.assertRaises(ValueError) as context:
            self.env["g2p.openid.vci.issuers"].issue_vc(
                {"format": "ldp_vc", "credential_definition": {"type": []}},
                jwt.encode(
                    {
                        "iss": "http://openg2p.local/auth",
                        "aud": "http://openg2p.local/api/v1/vci/credential",
                        "sub": self.registrant_national_id,
                        "exp": int(datetime.utcnow().timestamp()) + 5 * 60,
                    },
                    self.jwk,
                    algorithm="RS256",
                ),
            )
        self.assertTrue("Scope not found in auth token." in str(context.exception))

    @patch("requests.get")
    def test_issue_vc_invalid_id(self, mock_request):
        mock_request.side_effect = self.mock_request_get
        with self.assertRaises(ValueError) as context:
            self.env["g2p.openid.vci.issuers"].issue_vc(
                {"format": "ldp_vc", "credential_definition": {"type": []}},
                jwt.encode(
                    {
                        "scope": self.issuer_scope,
                        "iss": "http://openg2p.local/auth",
                        "aud": "http://openg2p.local/api/v1/vci/credential",
                        "sub": "random-value",
                        "exp": int(datetime.utcnow().timestamp()) + 5 * 60,
                    },
                    self.jwk,
                    algorithm="RS256",
                ),
            )
        self.assertTrue(
            "ID not found in DB. Invalid Subject Received in auth claims" in str(context.exception)
        )

    @patch("requests.get")
    def test_issue_vc_check_audience(self, mock_request):
        mock_request.side_effect = self.mock_request_get
        with self.assertRaises(ValueError) as context:
            self.issuer.auth_allowed_auds = "http://openg2p.local/api/v1/vci/credential"
            self.env["g2p.openid.vci.issuers"].issue_vc(
                {"format": "ldp_vc", "credential_definition": {"type": []}},
                jwt.encode(
                    {
                        "scope": self.issuer_scope,
                        "iss": "http://openg2p.local/auth",
                        "aud": ["http://random.url/credential"],
                        "sub": self.registrant_national_id,
                        "exp": int(datetime.utcnow().timestamp()) + 5 * 60,
                    },
                    self.jwk,
                    algorithm="RS256",
                ),
            )
        self.assertTrue("Invalid Audience" in str(context.exception))

    @patch("requests.get")
    def test_issue_vc_auth_expired(self, mock_request):
        mock_request.side_effect = self.mock_request_get
        with self.assertRaises(ValueError) as context:
            self.env["g2p.openid.vci.issuers"].issue_vc(
                {"format": "ldp_vc", "credential_definition": {"type": []}},
                jwt.encode(
                    {
                        "scope": self.issuer_scope,
                        "iss": "http://openg2p.local/auth",
                        "aud": "http://openg2p.local/api/v1/vci/credential",
                        "sub": self.registrant_national_id,
                        "exp": int(datetime.utcnow().timestamp()) - 5 * 60,
                    },
                    self.jwk,
                    algorithm="RS256",
                ),
            )
        self.assertTrue("Invalid Auth Token received" in str(context.exception))

    def test_get_issuer_metadata(self):
        res = self.env["g2p.openid.vci.issuers"].get_issuer_metadata_by_name()
        res = res["credentials_supported"][0]
        self.assertEqual("OpenG2PRegistryVerifiableCredential", res["id"])
        self.assertEqual("ldp_vc", res["format"])
        self.assertEqual(
            "Name", res["credential_definition"]["credentialSubject"]["fullName"]["display"][0]["name"]
        )

        # change issuer metadatas to dict
        self.issuer.issuer_metadata_text = (
            "{(.credential_type):"
            + self.issuer.issuer_metadata_text.strip().removeprefix("[").removesuffix("]")
            + "}"
        )
        self.issuer_2.issuer_metadata_text = (
            "{(.credential_type):"
            + self.issuer_2.issuer_metadata_text.strip().removeprefix("[").removesuffix("]")
            + "}"
        )

        res = self.env["g2p.openid.vci.issuers"].get_issuer_metadata_by_name()
        res = res["credential_configurations_supported"]["OpenG2PRegistryVerifiableCredential"]
        self.assertEqual("OpenG2PRegistryVerifiableCredential", res["id"])
        self.assertEqual("ldp_vc", res["format"])
        self.assertEqual(
            "Name", res["credential_definition"]["credentialSubject"]["fullName"]["display"][0]["name"]
        )

        self.issuer.issuer_metadata_text = '"Random"'

        res = self.env["g2p.openid.vci.issuers"].get_issuer_metadata_by_name(issuer_name="Test Issuer")
        self.assertEqual("http://openg2p.local", res.pop("credential_issuer"))
        self.assertEqual("http://openg2p.local/api/v1/vci/credential", res.pop("credential_endpoint"))
        self.assertEqual({}, res)

    def test_issuer_misc(self):
        self.env["g2p.openid.vci.issuers"].set_from_static_file_Registry(
            file_name="default_credential_format.jq"
        )
        self.env["g2p.openid.vci.issuers"].set_from_static_file_Registry(file_name="random_file.json")
        with self.assertRaises(TypeError):
            VCJSONEncoder().default(
                misc.file_open(os.path.join("g2p_openid_vci", "data", "default_contexts.json"))
            )
