from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _push_to_rabbitmq(self):
        """Push the record to RabbitMQ after applying JQ transformation."""
        configs = self.env["g2p.datashare.config.rabbitmq"].search(
            [("active", "=", True), ("data_source", "=", "registry")]
        )
        for rec in self:
            if rec.is_registrant:
                rec_data = rec.read()[0]
                for config in configs:
                    self.process_reg_id(config.id_type, rec_data)
                    transformed = config.transform_data(rec_data)
                    if transformed is not None:
                        config.publish(transformed)

    def process_reg_id(self, id_type, rec_data):
        if id_type.id:
            reg_id = self.env["g2p.reg.id"].search(
                [("id_type", "=", id_type.id), ("partner_id", "=", rec_data["id"])], limit=1
            )
            if reg_id:
                return rec_data.update({"reg_id_value": reg_id.value})

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
