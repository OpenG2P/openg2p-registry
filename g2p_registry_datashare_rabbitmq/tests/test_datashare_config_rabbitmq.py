import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestDatashareConfig(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.id_type = cls.env["g2p.id.type"].create({"name": "Datashare National ID"})
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner", "is_registrant": True})
        cls.reg_id = cls.env["g2p.reg.id"].create(
            {
                "partner_id": cls.partner.id,
                "id_type": cls.id_type.id,
                "value": "ABC123456",
            }
        )
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
                "transform_data_jq": """{"id": .id, "name": .name, "nationalID": .reg_id_value}""",
                "active": True,
                "data_source": "registry",
                "id_type": cls.id_type.id,
            }
        )

    def test_01_create_config(self):
        self.assertTrue(self.config)
        self.assertEqual(self.config.name, "Test Config")
        self.assertEqual(self.config.host, "localhost")
        self.assertEqual(self.config.data_source, "registry")
        self.assertEqual(self.config.id_type.name, "Datashare National ID")

    def test_02_transform_data_with_reg_id_value(self):
        rec_data = self.partner.read()[0]
        self.partner.process_reg_id(self.config.id_type, rec_data)

        self.assertIn("reg_id_value", rec_data)
        self.assertEqual(rec_data["reg_id_value"], "ABC123456")

        transformed = self.config.transform_data(rec_data)
        self.assertEqual(
            transformed,
            {"id": self.partner.id, "name": "Test Partner", "nationalID": "ABC123456"},
        )

    def test_03_invalid_jq_expression(self):
        rec_data = {"id": 1, "name": "Test Partner"}
        self.config.transform_data_jq = "invalid jq expression"
        transformed = self.config.transform_data(rec_data)
        self.assertIsNone(transformed)

    @patch("pika.BlockingConnection")
    def test_04_publish_data(self, mock_blocking_connection):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_blocking_connection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        rec_data = self.partner.read()[0]
        self.partner.process_reg_id(self.config.id_type, rec_data)
        self.config.transform_data_jq = """{"id": .id, "nationalID": .reg_id_value}"""
        transformed = self.config.transform_data(rec_data)
        self.config.publish(transformed)

        mock_channel.basic_publish.assert_called_once()
        args, kwargs = mock_channel.basic_publish.call_args
        self.assertEqual(kwargs["exchange"], "test_exchange")
        self.assertEqual(kwargs["routing_key"], "test_routing_key")
        self.assertEqual(
            json.loads(kwargs["body"]),
            {"id": self.partner.id, "nationalID": "ABC123456"},
        )

    def test_05_publish_with_failed_transformation(self):
        test_data = {"id": 1, "name": "Test Partner"}
        self.config.transform_data_jq = "invalid jq"
        result = self.config.publish(test_data)
        self.assertFalse(result)

    def test_06_multiple_data_sources(self):
        registry_config = self.env["g2p.datashare.config.rabbitmq"].create(
            {
                "name": "Registry Config",
                "host": "localhost",
                "port": 5672,
                "username": "guest",
                "password": "guest",
                "exchange": "registry_exchange",
                "routing_key": "registry_routing",
                "data_source": "registry",
            }
        )

        self.assertEqual(registry_config.data_source, "registry")
        self.assertEqual(self.config.data_source, "registry")
