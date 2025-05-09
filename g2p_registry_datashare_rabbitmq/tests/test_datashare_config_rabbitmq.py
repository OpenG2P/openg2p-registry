import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestDatashareConfig(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
                "transform_data_jq": """{"id": .id, "name": .name}""",
                "active": True,
                "data_source": "registry",
            }
        )

    def test_01_create_config(self):
        self.assertTrue(self.config)
        self.assertEqual(self.config.name, "Test Config")
        self.assertEqual(self.config.host, "localhost")
        self.assertEqual(self.config.data_source, "registry")

    def test_02_transform_data(self):
        test_data = {"id": 1, "name": "Test Partner", "email": "test@example.com", "phone": "1234567890"}
        self.config.transform_data_jq = """{"id": .id, "name": .name}"""
        transformed = self.config.transform_data(test_data)
        self.assertEqual(transformed, {"id": 1, "name": "Test Partner"})

        self.config.transform_data_jq = "{id, contact: {email, phone}}"
        transformed = self.config.transform_data(test_data)
        self.assertEqual(
            transformed, {"id": 1, "contact": {"email": "test@example.com", "phone": "1234567890"}}
        )

    def test_03_invalid_jq_expression(self):
        test_data = {"id": 1, "name": "Test Partner"}
        self.config.transform_data_jq = "invalid jq expression"
        transformed = self.config.transform_data(test_data)
        self.assertIsNone(transformed)

    @patch("pika.BlockingConnection")
    def test_04_publish_data(self, mock_blocking_connection):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_blocking_connection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        test_data = {"id": 1, "name": "Test Partner"}
        self.config.transform_data_jq = "{id, name}"
        transformed = self.config.transform_data(test_data)
        self.config.publish(transformed)

        mock_channel.basic_publish.assert_called_once()
        args, kwargs = mock_channel.basic_publish.call_args
        self.assertEqual(kwargs["exchange"], "test_exchange")
        self.assertEqual(kwargs["routing_key"], "test_routing_key")
        self.assertEqual(json.loads(kwargs["body"]), {"id": 1, "name": "Test Partner"})

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
