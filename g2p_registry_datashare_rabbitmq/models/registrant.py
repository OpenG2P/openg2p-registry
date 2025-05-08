from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _push_to_rabbitmq(self):
        """Push the record to RabbitMQ after applying JQ transformation."""
        configs = self.env["g2p.datashare.config.rabbitmq"].search([("active", "=", True)])
        for rec in self:
            if rec.is_registrant:
                rec_data = rec.read()[0]
                for config in configs:
                    transformed = config.transform_data(rec_data)
                    config.publish(transformed)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to push new records to RabbitMQ."""
        records = super().create(vals_list)
        records._push_to_rabbitmq()
        return records

    def write(self, vals):
        """Override write to push updated records to RabbitMQ."""
        res = super().write(vals)
        self._push_to_rabbitmq()
        return res
