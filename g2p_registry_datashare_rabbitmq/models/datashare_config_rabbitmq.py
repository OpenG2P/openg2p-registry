import json
import logging

import jq
import pika

from odoo import fields, models

from ..json_encoder import JSONEncoder

_logger = logging.getLogger(__name__)


class G2PDatashareConfigRabbitMQ(models.Model):
    _name = "g2p.datashare.config.rabbitmq"
    _description = "G2P Datashare Config RabbitMQ"

    name = fields.Char(required=True)
    host = fields.Char(required=True, default="localhost")
    port = fields.Char(required=True, default=5672)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    vhost = fields.Char(default="/")
    exchange = fields.Char(required=True)
    routing_key = fields.Char(required=True)

    data_source = fields.Selection(
        [
            ("registry", "Registry"),
        ],
        required=True,
        help="Specifies which data should be shared through this configuration",
    )

    id_type = fields.Many2one(
        "g2p.id.type",
        string="ID Type",
        help="ID Type to be used for the data",
    )

    transform_data_jq = fields.Text(
        string="Data Transform JQ Expression",
        default="""{}""",
        help="JQ expression to transform the res.partner record before sending to RabbitMQ.",
    )
    active = fields.Boolean(default=True)

    def _connect_to_rabbitmq(self):
        """Establish and return a RabbitMQ connection and channel."""
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
        )
        connection = pika.BlockingConnection(parameters)
        return connection, connection.channel()

    def transform_data(self, data):
        """Apply JQ transformation to the input data."""
        try:
            record_data = JSONEncoder.python_dict_to_json_dict(data)
            transformed = jq.first(self.transform_data_jq, record_data)
            if transformed is None:
                _logger.error("JQ transformation returned None for data: %s", data)
                return None
            return transformed
        except Exception as e:
            _logger.error("JQ transformation failed: %s", e)
            return None

    def publish(self, data):
        """Publish data to RabbitMQ after transforming it."""
        try:
            if data is None:
                _logger.error("Failed to transform data: %s", data)
                return False
            connection, channel = self._connect_to_rabbitmq()
            message = json.dumps(data)
            channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.routing_key,
                body=message,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )
            connection.close()
            _logger.debug("Published to RabbitMQ: %s", message)
        except Exception as e:
            _logger.error("RabbitMQ publish failed: %s", e)
