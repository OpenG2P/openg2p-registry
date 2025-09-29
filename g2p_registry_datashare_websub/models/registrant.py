import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        if not isinstance(vals, list):
            vals = [
                vals,
            ]
        for i in range(len(res)):
            if res[i].is_registrant:
                new_vals = vals[i].copy()
                new_vals["id"] = res[i].id
                event_type = "WEBSUB_GROUP_CREATED" if res[i].is_group else "WEBSUB_INDIVIDUAL_CREATED"

                _logger.info(
                    "WEBSUB PUBLISH TRIGGERED - CREATE - Partner: '%s' (ID: %s), Event: %s, Is Group: %s",
                    res[i].name,
                    res[i].id,
                    event_type,
                    res[i].is_group,
                )

                self.env["g2p.datashare.config.websub"].with_delay().publish_event(event_type, new_vals)
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.is_registrant:
                new_vals = vals.copy()
                new_vals["id"] = rec.id
                event_type = "WEBSUB_GROUP_UPDATED" if rec.is_group else "WEBSUB_INDIVIDUAL_UPDATED"

                _logger.info(
                    "WEBSUB PUBLISH TRIGGERED - UPDATE - Partner: '%s' (ID: %s), Event: %s, Is Group: %s",
                    rec.name,
                    rec.id,
                    event_type,
                    rec.is_group,
                )

                self.env["g2p.datashare.config.websub"].with_delay().publish_event(event_type, new_vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.is_registrant:
                event_type = "WEBSUB_GROUP_DELETED" if rec.is_group else "WEBSUB_INDIVIDUAL_DELETED"

                _logger.info(
                    "WEBSUB PUBLISH TRIGGERED - DELETE - Partner: '%s' (ID: %s), Event: %s, Is Group: %s",
                    rec.name,
                    rec.id,
                    event_type,
                    rec.is_group,
                )

                self.env["g2p.datashare.config.websub"].with_delay().publish_event(
                    event_type, dict(id=rec.id)
                )
        return super().unlink()
