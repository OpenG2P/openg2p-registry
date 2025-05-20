from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentStore(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        # Set up a sample storage backend
        self.storage_backend = self.env["storage.backend"].create({"name": "Test Backend"})
        self.enc_provider = self.env["g2p.encryption.provider"].create({"name": "Test Enc Provider"})

    # TODO.
