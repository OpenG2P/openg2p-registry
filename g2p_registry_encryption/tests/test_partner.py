import json
from unittest.mock import patch

from odoo.tests import TransactionCase

from odoo.addons.g2p_encryption.models.encryption_provider import G2PEncryptionProvider
from odoo.addons.g2p_registry_encryption.models.encryption_provider import RegistryEncryptionProvider


class TestEncryptedPartner(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_model = self.env["res.partner"]
        self.provider_model = self.env["g2p.encryption.provider"]

        self.registry_provider = self.provider_model.create(
            {
                "name": "Test Provider",
                "type": "keymanager",
            }
        )
        self.registry_provider.set_registry_provider(self.registry_provider.id)

        self.env["ir.config_parameter"].sudo().set_param("g2p_registry_encryption.encrypt_registry", True)
        self.env["ir.config_parameter"].sudo().set_param("g2p_registry_encryption.decrypt_registry", True)

    @patch.object(
        RegistryEncryptionProvider,
        "get_registry_fields_set_to_enc",
        return_value={
            "name",
            "family_name",
            "given_name",
            "addl_name",
            "display_name",
            "address",
            "birth_place",
        },
    )
    @patch.object(G2PEncryptionProvider, "encrypt_data", side_effect=lambda data: data[::-1])
    @patch.object(G2PEncryptionProvider, "decrypt_data", side_effect=lambda data: data[::-1])
    def test_create_encrypted_partner(self, mock_get_fields, mock_encrypt_data, mock_decrypt_data):
        vals = {
            "name": "John Doe",
            "family_name": "Doe",
            "given_name": "John",
            "addl_name": "Smith",
            "display_name": "John Doe",
            "address": "123 Main St",
            "birth_place": "City A",
            "is_registrant": True,
        }

        partner = self.partner_model.create(vals)

        self.assertTrue(partner.is_encrypted)
        self.assertTrue(partner.encrypted_val)

        decrypted_data = json.loads(self.registry_provider.decrypt_data(partner.encrypted_val))

        self.assertEqual(decrypted_data["name"], "John Doe")
        self.assertEqual(decrypted_data["family_name"], "Doe")

    @patch.object(G2PEncryptionProvider, "encrypt_data", side_effect=lambda data: data[::-1])
    @patch.object(G2PEncryptionProvider, "decrypt_data", side_effect=lambda data: data[::-1])
    def test_write_encrypted_partner(self, mock_encrypt_data, mock_decrypt_data):
        partner = self.partner_model.create(
            {
                "name": "John Doe",
                "is_registrant": True,
            }
        )

        partner.write(
            {
                "name": "John Updated",
                "address": "New Address",
            }
        )

        self.assertTrue(partner.is_encrypted)
        decrypted_data = json.loads(self.registry_provider.decrypt_data(partner.encrypted_val))
        self.assertEqual(decrypted_data["name"], "John Updated")
        self.assertEqual(decrypted_data["address"], "New Address")

    def test_create_partner_without_encryption(self):
        self.env["ir.config_parameter"].sudo().set_param("g2p_registry_encryption.encrypt_registry", False)
        partner = self.partner_model.create({"name": "John Doe"})
        self.assertFalse(partner.is_encrypted)
        self.assertFalse(partner.encrypted_val)
