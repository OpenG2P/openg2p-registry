from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentStore(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        # Set up a sample storage backend
        self.storage_backend = self.env["storage.backend"].create({"name": "Test Backend"})
        self.enc_provider = self.env["g2p.encryption.provider"].create({"name": "Test Enc Provider"})

    def test_get_encryption_provider_always_encrypt(self):
        self.storage_backend.encryption_strategy = "always_encrypt"
        self.storage_backend.encryption_provider_id = self.enc_provider.id
        self.assertEqual(self.enc_provider, self.storage_backend.get_encryption_provider())

    def test_get_encryption_provider_none(self):
        self.storage_backend.encryption_strategy = None
        self.assertFalse(self.storage_backend.get_encryption_provider())

    def test_get_decryption_provider_always_decrypt(self):
        self.storage_backend.viewing_decryption_strategy = "always_decrypt"
        self.storage_backend.encryption_provider_id = self.enc_provider.id
        self.assertEqual(self.enc_provider, self.storage_backend.get_decryption_provider())

    def test_get_decryption_provider_none(self):
        self.storage_backend.viewing_decryption_strategy = None
        self.assertFalse(self.storage_backend.get_decryption_provider())
