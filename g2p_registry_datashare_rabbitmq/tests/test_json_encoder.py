from datetime import date, datetime

from odoo.tests.common import TransactionCase


class TestJSONEncoder(TransactionCase):
    def test_01_datetime_encoding(self):
        """Test encoding of datetime objects"""
        test_data = {
            "create_date": datetime.now(),
            "date": date.today(),
        }

        # Create config with JQ expression that includes dates
        config = self.env["g2p.datashare.config.rabbitmq"].create(
            {
                "name": "Test Config",
                "host": "localhost",
                "port": 5672,
                "username": "guest",
                "password": "guest",
                "exchange": "test",
                "routing_key": "test",
                "transform_data_jq": ".",
            }
        )

        # Transform and verify
        transformed = config.transform_data(test_data)
        self.assertIsInstance(transformed["create_date"], str)
        self.assertIsInstance(transformed["date"], str)
