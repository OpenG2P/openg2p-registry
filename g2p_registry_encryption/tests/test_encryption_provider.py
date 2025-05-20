from odoo.tests import TransactionCase


class TestRegistryEncryptionProvider(TransactionCase):
    def setUp(self):
        super().setUp()
        self.registry_provider = self.env["g2p.encryption.provider"].create(
            {
                "name": "Registry Provider",
                "type": "keymanager",
            }
        )

    def test_get_registry_fields_set_to_enc(self):
        fields_to_enc = self.registry_provider.get_registry_fields_set_to_enc()
        expected_fields = {
            "name",
            "family_name",
            "given_name",
            "addl_name",
            "display_name",
            "address",
            "birth_place",
        }
        self.assertEqual(fields_to_enc, expected_fields)

    def test_set_registry_provider(self):
        self.registry_provider.set_registry_provider(self.registry_provider.id)
        config_param = (
            self.env["ir.config_parameter"].sudo().get_param("g2p_registry_encryption.encryption_provider_id")
        )
        self.assertEqual(config_param, str(self.registry_provider.id))

    def test_get_registry_provider(self):
        self.registry_provider.set_registry_provider(self.registry_provider.id)
        provider = self.registry_provider.get_registry_provider()
        self.assertEqual(provider.id, self.registry_provider.id)
