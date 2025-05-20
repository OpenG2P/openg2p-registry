import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from odoo.tests import TransactionCase


class TestKeymanagerEncryptionProvider(TransactionCase):
    def setUp(self):
        super().setUp()
        self.provider = self.env["g2p.encryption.provider"].create(
            {
                "name": "Test Keymanager",
                "type": "keymanager",
                "keymanager_encrypt_application_id": "TEST_APP",
                "keymanager_encrypt_reference_id": "TEST_REF",
                "keymanager_sign_application_id": "TEST_SIGN_APP",
                "keymanager_sign_reference_id": "TEST_SIGN_REF",
                "keymanager_encrypt_salt": "test_salt",
                "keymanager_encrypt_aad": "test_aad",
            }
        )

        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.cert = self._generate_test_certificate()

        patcher = patch(
            "odoo.addons.g2p_encryption_keymanager.models.encryption_provider.KeymanagerEncryptionProvider.km_get_access_token",
            return_value="test_token",
        )
        self.mock_get_token = patcher.start()
        self.addCleanup(patcher.stop)

    def _generate_test_certificate(self):
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test Certificate")])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(self.private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=10))
            .sign(self.private_key, hashes.SHA256())
        )

        return cert

    @patch("requests.post")
    def test_encrypt_data(self, mock_post):
        test_data = b"test data"
        encrypted_data = b"encrypted data"
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": {"data": base64.urlsafe_b64encode(encrypted_data).decode().rstrip("=")}
        }
        mock_post.return_value = mock_response

        result = self.provider.encrypt_data_keymanager(test_data)
        assert result == encrypted_data

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "encrypt" in call_args[0][0]

    @patch("requests.post")
    def test_decrypt_data(self, mock_post):
        encrypted_data = b"encrypted data"
        decrypted_data = b"test data"
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": {"data": base64.urlsafe_b64encode(decrypted_data).decode().rstrip("=")}
        }
        mock_post.return_value = mock_response

        result = self.provider.decrypt_data_keymanager(encrypted_data)
        assert result == decrypted_data

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "decrypt" in call_args[0][0]

    @patch("requests.post")
    def test_jwt_sign(self, mock_post):
        test_data = {"test": "data"}
        signed_jwt = "signed.jwt.token"
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"jwtSignedData": signed_jwt}}
        mock_post.return_value = mock_response

        result = self.provider.jwt_sign_keymanager(test_data)
        assert result == signed_jwt

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "jwtSign" in call_args[0][0]

    @patch("requests.post")
    def test_jwt_verify(self, mock_post):
        jwt_token = "test.jwt.token"
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"signatureValid": True}}
        mock_post.return_value = mock_response

        with patch("jose.jwt.get_unverified_claims", return_value={"test": "claim"}):
            result = self.provider.jwt_verify_keymanager(jwt_token)
            assert result == {"test": "claim"}

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "jwtVerify" in call_args[0][0]

    @patch("requests.get")
    def test_get_jwks(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": {
                "allCertificates": [
                    {
                        "certificateData": self.cert.public_bytes(serialization.Encoding.PEM).decode(),
                        "keyId": "test_key_id",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = self.provider.get_jwks_keymanager()
        assert "keys" in result
        assert isinstance(result["keys"], list)
        assert len(result["keys"]) > 0
        assert "kid" in result["keys"][0]
        assert result["keys"][0]["kid"] == "test_key_id"

    def test_url_safe_b64_encode_decode(self):
        test_data = b"test data with special chars !@#$%^&*()"

        encoded = self.provider.km_urlsafe_b64encode(test_data)
        assert isinstance(encoded, str)
        assert "=" not in encoded

        decoded = self.provider.km_urlsafe_b64decode(encoded)
        assert decoded == test_data
