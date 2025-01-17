from odoo import api, models


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
                self.env["g2p.datashare.config.websub"].with_delay().publish_event(
                    "WEBSUB_GROUP_CREATED" if res[i].is_group else "WEBSUB_INDIVIDUAL_CREATED", new_vals
                )
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.is_registrant:
                new_vals = vals.copy()
                new_vals["id"] = rec.id
                self.env["g2p.datashare.config.websub"].with_delay().publish_event(
                    "WEBSUB_GROUP_UPDATED" if rec.is_group else "WEBSUB_INDIVIDUAL_UPDATED", new_vals
                )
        return res

    def unlink(self):
        for rec in self:
            if rec.is_registrant:
                self.env["g2p.datashare.config.websub"].with_delay().publish_event(
                    "WEBSUB_GROUP_DELETED" if rec.is_group else "WEBSUB_INDIVIDUAL_DELETED", dict(id=rec.id)
                )
        return super().unlink()
