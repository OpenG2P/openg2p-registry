import json
from datetime import datetime
from unittest.mock import patch

from jose import jwt
from jwcrypto import jwk

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.g2p_encryption.models.encryption_provider import G2PEncryptionProvider


@tagged("-at_install", "post_install")
class TestVCIIssuerRegistryGroup(TransactionCase):
    """Test cases for VCI Issuer Registry Group functionality"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self._setup_base_config()
        self._setup_membership_kinds()
        self._setup_test_data()
        self._setup_vci_issuer()
        self._setup_jwt_components()
        self._setup_mock_jsonld()

    def _setup_base_config(self):
        """Configure base system settings"""
        # Set the base URL for the system
        self.env["ir.config_parameter"].set_param("web.base.url", "http://openg2p.local")

        # Check if the id_type exists, if not, create one
        self.id_type = self.env["g2p.id.type"].search([("name", "=", "National ID")], limit=1)
        if not self.id_type:
            self.id_type = self.env["g2p.id.type"].create(
                {
                    "name": "National ID",
                }
            )

    def _setup_membership_kinds(self):
        """Set up membership kinds for testing"""
        MembershipKind = self.env["g2p.group.membership.kind"]

        # Search for "Head" kind
        self.head_kind = MembershipKind.search([("name", "=", "Head")], limit=1)
        if not self.head_kind:
            self.head_kind = MembershipKind.create({"name": "Head"})

        # Search for "Member" kind
        self.member_kind = MembershipKind.search([("name", "=", "Member")], limit=1)
        if not self.member_kind:
            self.member_kind = MembershipKind.create(
                {"name": "Test Member Kind " + str(int(datetime.now().timestamp()))}
            )

    def _setup_test_data(self):
        """Set up test registrant, group and membership data"""
        # Set up test data
        self.registrant = self.env["res.partner"].create(
            {"name": "Test Individual", "is_group": False, "is_registrant": True}
        )

        # Create ID for registrant
        self.env["g2p.reg.id"].create(
            {"partner_id": self.registrant.id, "id_type": self.id_type.id, "value": "12345678"}
        )

        # Create test group
        self.group = self.env["res.partner"].create(
            {
                "name": "Test Group",
                "is_group": True,
                "is_registrant": True,
                "address": json.dumps({"street_address": "123 Test St", "locality": "Test City"}),
            }
        )

        # Create group membership
        self.membership = self.env["g2p.group.membership"].create(
            {"group": self.group.id, "individual": self.registrant.id, "kind": [(4, self.head_kind.id)]}
        )

    def _setup_vci_issuer(self):
        """Set up VCI issuer configuration"""
        # Create VCI issuer with correct configuration
        self.issuer = self.env["g2p.openid.vci.issuers"].create(
            {
                "name": "Test Group Issuer",
                "issuer_type": "Registry_Group",
                "scope": "group_vc",
                "auth_sub_id_type_id": self.id_type.id,
                "auth_allowed_issuers": "http://openg2p.local/auth",
                "credential_type": "OpenG2PRegistryGroupVerifiableCredential",
                "supported_format": "ldp_vc",
                "credential_format": """
            {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    (.web_base_url + "/api/v1/vci/.well-known/contexts.json")
                ],
                "id": .vc_id,
                "type": ["VerifiableCredential", .issuer.credential_type],
                "issuer": .issuer.unique_issuer_id,
                "issuanceDate": .curr_datetime,
                "credentialSubject": {
                    "id": (.web_base_url + "/api/v1/registry/group/" + (.group.id | tostring)),
                    "group": .group
                }
            }
            """,  # Using proper jq filter format
            }
        )

    def _setup_jwt_components(self):
        """Set up JWT related test components"""
        # Create test JWT key using jwcrypto with proper PEM export
        self.test_jwk = jwk.JWK.generate(kty="RSA", size=2048, kid="test-key-1", alg="RS256", use="sig")

        # Export private key in PEM format for JWT signing
        private_key = self.test_jwk.export_to_pem(private_key=True, password=None)

        # Export public key for verification
        self.public_jwk = json.loads(self.test_jwk.export_public())

        # Set up JWT claims with matching scope
        self.test_jwt_claims = {
            "scope": "group_vc",  # Match this with the issuer scope
            "iss": "http://openg2p.local/auth",
            "aud": "http://openg2p.local/api/v1/vci/credential",
            "sub": "12345678",  # This matches the head member's ID
            "exp": 9999999999,
            "iat": 1619999999,
        }

        # Create actual JWT token using PEM private key
        self.test_token = jwt.encode(
            self.test_jwt_claims, private_key, algorithm="RS256", headers={"kid": "test-key-1"}
        )

    def _setup_mock_jsonld(self):
        """Set up mock JSON-LD context"""
        # Mock JSON-LD context for testing
        self.mock_jsonld_context = {
            "contextUrl": None,
            "documentUrl": None,
            "document": {
                "@context": {
                    "@version": 1.1,
                    "id": "@id",
                    "type": "@type",
                    "OpenG2PRegistryGroupVerifiableCredential": {
                        "@id": "https://w3id.org/openg2p#OpenG2PRegistryGroupVerifiableCredential",
                        "@context": {
                            "@version": 1.1,
                            "id": "@id",
                            "type": "@type",
                            "group": "https://w3id.org/openg2p#group",
                        },
                    },
                }
            },
        }

    # Basic Configuration Tests
    @patch.object(G2PEncryptionProvider, "jwt_verify")
    def test_credential_type_default(self, mock_jwt_verify):
        """Test that the default credential type is correctly set for group issuer.

        Verifies that the credential_type field is properly initialized with
        'OpenG2PRegistryGroupVerifiableCredential' when creating a new issuer.
        """
        mock_jwt_verify.return_value = self.test_jwt_claims

        self.assertEqual(self.issuer.credential_type, "OpenG2PRegistryGroupVerifiableCredential")

    def test_set_default_credential_type(self):
        """Test setting default credential type for a new issuer.

        Verifies that when creating a new issuer without a credential type,
        calling set_default_credential_type_Registry_Group() properly sets
        the default credential type to 'OpenG2PRegistryGroupVerifiableCredential'.
        """
        # Create a new issuer without credential type
        new_issuer = self.env["g2p.openid.vci.issuers"].create(
            {
                "name": "Test Group Issuer 2",
                "issuer_type": "Registry_Group",
                "scope": "group_vc",
                "auth_sub_id_type_id": self.id_type.id,
                "auth_allowed_issuers": "http://openg2p.local/auth",
            }
        )

        # Call the method to set default credential type
        new_issuer.set_default_credential_type_Registry_Group()

        self.assertEqual(new_issuer.credential_type, "OpenG2PRegistryGroupVerifiableCredential")

    # VC Issuance Tests
    @patch("requests.get")
    @patch.object(G2PEncryptionProvider, "jwt_verify")
    @patch.object(G2PEncryptionProvider, "jwt_sign")
    @patch("pyld.jsonld.load_document")
    def test_issue_vc_success(self, mock_jsonld_loader, mock_jwt_sign, mock_jwt_verify, mock_request):
        """Test successful issuance of a Verifiable Credential.

        This test verifies the complete flow of issuing a VC including:
        - Proper JWT verification
        - Correct JSON-LD context loading
        - Valid credential structure generation
        - Proper inclusion of group details in the credential
        - Correct formatting of the response

        Args:
            mock_jsonld_loader: Mock for JSON-LD document loader
            mock_jwt_sign: Mock for JWT signing
            mock_jwt_verify: Mock for JWT verification
            mock_request: Mock for HTTP requests
        """
        # Mock JSON-LD document loader
        mock_jsonld_loader.return_value = self.mock_jsonld_context

        # Mock JWT verification with correct scope
        self.test_jwt_claims["scope"] = "group_vc"
        mock_jwt_verify.return_value = self.test_jwt_claims

        # Mock JWKS endpoint
        mock_request.return_value.json.return_value = {"keys": [self.public_jwk]}

        # Mock JWT signing with a complete credential
        mock_jwt_sign.return_value = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "http://openg2p.local/api/v1/vci/.well-known/contexts.json",
            ],
            "type": ["VerifiableCredential", "OpenG2PRegistryGroupVerifiableCredential"],
            "credentialSubject": {
                "id": f"http://openg2p.local/api/v1/registry/group/{self.group.id}",
                "group": {
                    "name": "Test Group",
                    "address": {"street_address": "123 Test St", "locality": "Test City"},
                },
            },
        }

        # Test VC issuance
        result = self.issuer.issue_vc(
            {
                "format": "ldp_vc",
                "credential_definition": {
                    "type": ["VerifiableCredential", "OpenG2PRegistryGroupVerifiableCredential"]
                },
            },
            self.test_token,
        )

        # Verify response structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["format"], "ldp_vc")

        # Verify the credential structure
        credential = result["credential"]
        self.assertIn("@context", credential)
        self.assertIn("type", credential)
        self.assertIn("credentialSubject", credential)

        # Verify credential subject content
        subject = credential["credentialSubject"]
        self.assertIn("id", subject)
        self.assertIn("group", subject)
        self.assertEqual(subject["group"]["name"], "Test Group")
        self.assertEqual(subject["id"], f"http://openg2p.local/api/v1/registry/group/{self.group.id}")

    # Error Cases
    @patch("requests.get")
    @patch.object(G2PEncryptionProvider, "jwt_verify")
    @patch.object(G2PEncryptionProvider, "jwt_sign")
    @patch("pyld.jsonld.load_document")
    def test_issue_vc_no_reg_id(self, mock_jsonld_loader, mock_jwt_sign, mock_jwt_verify, mock_request):
        """Test VC issuance failure when registration ID doesn't exist.

        Verifies that the VC issuance process fails appropriately when:
        - The JWT subject ID doesn't match any registration ID in the database
        - Proper error message is raised

        Args:
            mock_jsonld_loader: Mock for JSON-LD document loader
            mock_jwt_sign: Mock for JWT signing
            mock_jwt_verify: Mock for JWT verification
            mock_request: Mock for HTTP requests
        """
        # Mock JSON-LD document loader
        mock_jsonld_loader.return_value = self.mock_jsonld_context

        # Mock JWT signing
        mock_jwt_sign.return_value = "mocked.jwt.token"

        # Mock JWKS endpoint
        mock_request.return_value.json.return_value = {"keys": [self.public_jwk]}

        # Mock JWT verification with non-existent ID
        self.test_jwt_claims["sub"] = "non_existent_id"
        mock_jwt_verify.return_value = self.test_jwt_claims

        # Delete any existing reg_id records for this test
        self.env["g2p.reg.id"].search([]).unlink()

        with self.assertRaisesRegex(
            ValueError, "ID not found in DB. Invalid Subject Received in auth claims"
        ):
            self.issuer.issue_vc(
                {
                    "format": "ldp_vc",
                    "credential_definition": {
                        "type": ["VerifiableCredential", "OpenG2PRegistryGroupVerifiableCredential"]
                    },
                },
                self.test_token,
            )

    @patch("requests.get")
    @patch.object(G2PEncryptionProvider, "jwt_verify")
    def test_issue_vc_not_head(self, mock_jwt_verify, mock_request):
        """Test VC issuance failure when requester is not group head.

        Verifies that the VC issuance process fails appropriately when:
        - The individual requesting the VC is not marked as the head of the group
        - The membership kind is set to 'member' instead of 'head'
        - Proper error message is raised

        Args:
            mock_jwt_verify: Mock for JWT verification
            mock_request: Mock for HTTP requests
        """
        # Change membership kind to member instead of head
        self.membership.write(
            {
                "kind": [(6, 0, [self.member_kind.id])]  # Replace head kind with member kind
            }
        )

        # Mock JWKS endpoint
        mock_request.return_value.json.return_value = {"keys": [self.public_jwk]}

        mock_jwt_verify.return_value = self.test_jwt_claims

        with self.assertRaisesRegex(ValueError, "Individual is not head of any group"):
            self.issuer.issue_vc(
                {
                    "format": "ldp_vc",
                    "credential_definition": {
                        "type": ["VerifiableCredential", "OpenG2PRegistryGroupVerifiableCredential"]
                    },
                },
                self.test_token,
            )
