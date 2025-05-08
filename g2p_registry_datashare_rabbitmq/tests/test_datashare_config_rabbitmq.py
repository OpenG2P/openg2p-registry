import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestDatashareConfig(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test config
        cls.config = cls.env["g2p.datashare.config"].create(
            {
                "name": "Test Config",
                "host": "localhost",
                "port": 5672,
                "username": "guest",
                "password": "guest",
                "vhost": "/",
                "exchange": "test_exchange",
                "routing_key": "test_routing_key",
                "transform_data_jq": "{id, name}",
                "active": True,
            }
        )

    def test_01_create_config(self):
        """Test creating a configuration"""
        self.assertTrue(self.config)
        self.assertEqual(self.config.name, "Test Config")
        self.assertEqual(self.config.host, "localhost")

    def test_02_required_fields(self):
        """Test required fields validation"""
        with self.assertRaises(ValidationError):
            self.env["g2p.datashare.config"].create(
                {
                    "name": "Invalid Config",
                    # Missing required fields
                }
            )

    def test_03_transform_data(self):
        """Test JQ transformation of data"""
        test_data = {"id": 1, "name": "Test Partner", "email": "test@example.com", "phone": "1234567890"}

        # Test with simple JQ expression
        self.config.transform_data_jq = "{id, name}"
        transformed = self.config.transform_data(test_data)
        self.assertEqual(transformed, {"id": 1, "name": "Test Partner"})

        # Test with complex JQ expression
        self.config.transform_data_jq = "{id, contact: {email, phone}}"
        transformed = self.config.transform_data(test_data)
        self.assertEqual(
            transformed, {"id": 1, "contact": {"email": "test@example.com", "phone": "1234567890"}}
        )

    def test_04_invalid_jq_expression(self):
        """Test handling of invalid JQ expressions"""
        test_data = {"id": 1, "name": "Test Partner"}

        # Test with invalid JQ expression
        self.config.transform_data_jq = "invalid jq expression"
        transformed = self.config.transform_data(test_data)

        # Should return None on error
        self.assertIsNone(transformed)

    @patch("pika.BlockingConnection")
    def test_05_publish_data(self, mock_connection):
        """Test publishing data"""
        # Mock the connection and channel
        mock_channel = MagicMock()
        mock_connection.return_value.__enter__.return_value.channel.return_value = mock_channel

        # Test data
        test_data = {"id": 1, "name": "Test Partner"}

        # Transform and publish data
        transformed = self.config.transform_data(test_data)
        self.config.publish(transformed)

        # Verify the message was published
        mock_channel.basic_publish.assert_called_once()
        call_args = mock_channel.basic_publish.call_args[1]
        self.assertEqual(call_args["exchange"], "test_exchange")
        self.assertEqual(call_args["routing_key"], "test_routing_key")
        self.assertEqual(json.loads(call_args["body"]), {"id": 1, "name": "Test Partner"})

    def test_06_publish_with_failed_transformation(self):
        """Test publishing when transformation fails"""
        test_data = {"id": 1, "name": "Test Partner"}
        self.config.transform_data_jq = "invalid jq"

        # Should not publish if transformation fails
        result = self.config.publish(test_data)
        self.assertFalse(result)
