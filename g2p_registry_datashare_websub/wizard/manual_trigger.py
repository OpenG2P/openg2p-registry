from odoo import _, fields, models
from odoo.tools import safe_eval


class G2PDatashareConfigWebsubExtraField(models.TransientModel):
    _name = "g2p.datashare.config.websub.manual.trigger"
    _description = "G2P Datashare Config WebSub Manual Trigger"

    config_id = fields.Many2one("g2p.datashare.config.websub")

    domain = fields.Text(string="Filter")

    def publish_records_manually_trigger(self):
        self.ensure_one()
        self.with_delay().publish_records_by_ids()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Websub Manual Publish"),
                "message": _("Records manual publishing started."),
                "sticky": True,
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def publish_records_by_ids(self):
        domain = safe_eval.safe_eval(self.domain)
        partner_ids = self.env["res.partner"].search(domain).ids
        for partner_id in partner_ids:
            self.config_id.publish_by_publisher({"id": partner_id}, condition_override="true")
