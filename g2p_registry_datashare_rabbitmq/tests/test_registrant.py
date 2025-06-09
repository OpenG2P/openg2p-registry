from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestRegistrant(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create ID type
        cls.id_type = cls.env["g2p.id.type"].create({"name": "Datashare National ID"})

        # Create test config
        cls.config = cls.env["g2p.datashare.config.rabbitmq"].create(
            {
                "name": "Test Config",
                "host": "localhost",
                "port": 5672,
                "username": "guest",
                "password": "guest",
                "vhost": "/",
                "exchange": "test_exchange",
                "routing_key": "test_routing_key",
                "transform_data_jq": """{id, name, reg_id_value}""",
                "active": True,
                "data_source": "registry",
                "id_type": cls.id_type.id,
            }
        )

    def test_01_create_registrant(self):
        """Test creating a registrant and verify push"""
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            registrant = self.env["res.partner"].create(
                {
                    "name": "Test Registrant",
                    "is_registrant": True,
                    "is_group": False,
                    "email": "test@example.com",
                }
            )
            self.env["g2p.reg.id"].create(
                {
                    "partner_id": registrant.id,
                    "id_type": self.id_type.id,
                    "value": "ABC123456",
                }
            )

            registrant._push_to_rabbitmq()

            mock_publish.assert_called()
            published_data = mock_publish.call_args[0][0]
            self.assertEqual(published_data["name"], "Test Registrant")
            self.assertEqual(published_data["reg_id_value"], "ABC123456")

    def test_02_update_registrant(self):
        """Test updating a registrant and verify push"""
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            registrant = self.env["res.partner"].create(
                {
                    "name": "Initial Name",
                    "is_registrant": True,
                    "is_group": False,
                }
            )
            self.env["g2p.reg.id"].create(
                {
                    "partner_id": registrant.id,
                    "id_type": self.id_type.id,
                    "value": "XYZ999",
                }
            )

            registrant.write({"name": "Updated Registrant"})

            self.assertEqual(mock_publish.call_count, 2)
            last_published_data = mock_publish.call_args[0][0]
            self.assertEqual(last_published_data["name"], "Updated Registrant")
            self.assertEqual(last_published_data["reg_id_value"], "XYZ999")

    def test_03_group_registrant(self):
        """Test that group registrants are pushed"""
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            self.env["res.partner"].create(
                {
                    "name": "Test Group",
                    "is_registrant": True,
                    "is_group": True,
                    "reg_ids": [
                        (
                            0,
                            0,
                            {
                                "id_type": self.id_type.id,
                                "value": "GROUP456",
                            },
                        )
                    ],
                }
            )
            mock_publish.assert_called_once()
            data = mock_publish.call_args[0][0]
            self.assertEqual(data["reg_id_value"], "GROUP456")

    def test_04_non_registrant(self):
        """Test that non-registrants are not pushed"""
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            self.env["res.partner"].create(
                {
                    "name": "Test Partner",
                    "is_registrant": False,
                    "is_group": False,
                }
            )
            mock_publish.assert_not_called()

    def test_05_bulk_create_registrants(self):
        """Test bulk creation of registrants"""
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            partners = self.env["res.partner"].create(
                [
                    {"name": "Registrant 1", "is_registrant": True, "is_group": False},
                    {"name": "Registrant 2", "is_registrant": True, "is_group": False},
                ]
            )

            for idx, partner in enumerate(partners, start=1):
                self.env["g2p.reg.id"].create(
                    {
                        "partner_id": partner.id,
                        "id_type": self.id_type.id,
                        "value": f"VAL{idx}",
                    }
                )

            self.assertEqual(mock_publish.call_count, 2)

    def test_06_failed_transformation(self):
        """Test handling of failed JQ transformation"""
        self.config.transform_data_jq = "invalid jq"
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            registrant = self.env["res.partner"].create(
                {"name": "Bad Transform", "is_registrant": True, "is_group": False}
            )
            self.env["g2p.reg.id"].create(
                {
                    "partner_id": registrant.id,
                    "id_type": self.id_type.id,
                    "value": "FAIL123",
                }
            )
            registrant._push_to_rabbitmq()
            mock_publish.assert_not_called()
