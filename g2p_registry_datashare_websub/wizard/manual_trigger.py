import logging

from odoo import _, fields, models
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class G2PDatashareConfigWebsubExtraField(models.TransientModel):
    _name = "g2p.datashare.config.websub.manual.trigger"
    _description = "G2P Datashare Config WebSub Manual Trigger"

    config_id = fields.Many2one("g2p.datashare.config.websub")
    domain = fields.Text()

    # Batch processing fields
    batch_size = fields.Integer(default=100, required=True)

    def publish_records_manually_trigger(self):
        self.ensure_one()

        _logger.info(
            "MANUAL WEBSUB PUBLISH TRIGGERED - Config: '%s' (ID: %s), Domain: %s, Batch Size: %s",
            self.config_id.name,
            self.config_id.id,
            self.domain,
            self.batch_size,
        )

        # Get total count of partners to process
        domain = safe_eval.safe_eval(self.domain) if self.domain else [("is_registrant", "=", True)]
        total_count = self.env["res.partner"].search_count(domain)

        if total_count == 0:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Records Found"),
                    "message": _("No partners found matching the criteria."),
                    "sticky": True,
                    "type": "warning",
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }

        # Create a batch publish record and start it immediately
        batch_record = self.env["g2p.websub.batch.publish"].create(
            {
                "config_id": self.config_id.id,
                "batch_size": self.batch_size,
                "partner_domain": self.domain or "[('is_registrant', '=', True)]",
                "total_records": total_count,
                "state": "running",
                "start_time": fields.Datetime.now(),
                "result_message": f"Starting batch publish for {total_count} partners...",
            }
        )

        # Start the batch processing job immediately
        batch_record.with_delay()._process_batch_publish()

        return {
            "type": "ir.actions.act_window",
            "name": _("Batch Publish Started"),
            "res_model": "g2p.websub.batch.publish",
            "res_id": batch_record.id,
            "view_mode": "form",
            "target": "current",
            "context": {"create": False},
        }
