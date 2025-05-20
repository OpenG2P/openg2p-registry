from odoo.tests import TransactionCase


class TestG2PEncryptionProvider(TransactionCase):
    def setUp(self):
        super().setUp()

        self.provider = self.env["g2p.encryption.provider"].create(
            {
                "name": "Test Keymanager",
                "type": "",
            }
        )

    def test_encrypt_data_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.provider.encrypt_data(b"data")

    def test_decrypt_data_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.provider.decrypt_data(b"data")

    def test_jwt_sign_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.provider.jwt_sign("data")

    def test_jwt_verify_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.provider.jwt_verify("data")

    def test_get_jwks_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.provider.get_jwks()
