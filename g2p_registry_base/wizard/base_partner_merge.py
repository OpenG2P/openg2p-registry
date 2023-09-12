import functools
import logging
import psycopg2

from odoo import api, models
from odoo.tools import mute_logger

_logger = logging.getLogger("odoo.addons.base.partner.merge")


class MyCustomPartnerMerge(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"
    _description = "Custom Partner Merge Wizard"

    @api.model
    def _update_reference_fields(self, src_partners, dst_partner):
        """Update all reference fields from the src_partner to dst_partner.
        :param src_partners : merge source res.partner recordset (does not include destination one)
        :param dst_partner : record of destination res.partner
        """
        _logger.debug(
            "_update_reference_fields for dst_partner: %s for src_partners: %r",
            dst_partner.id,
            src_partners.ids,
        )

        def update_records(model, src, field_model="model", field_id="res_id"):
            Model = self.env[model] if model in self.env else None
            if Model is None:
                return
            records = Model.sudo().search(
                [(field_model, "=", "res.partner"), (field_id, "=", src.id)]
            )
            try:
                with mute_logger("odoo.sql_db"), self._cr.savepoint():
                    records.sudo().write({field_id: dst_partner.id})
                    records.flush()
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent partner_id is useless, better delete it
                records.sudo().unlink()

        update_records = functools.partial(update_records)

        for partner in src_partners:
            update_records("calendar", src=partner, field_model="model_id.model")
            update_records("ir.attachment", src=partner, field_model="res_model")
            update_records("mail.followers", src=partner, field_model="res_model")
            update_records("mail.activity", src=partner, field_model="res_model")
            update_records("mail.message", src=partner)
            update_records("ir.model.data", src=partner)

        records = (
            self.env["ir.model.fields"].sudo().search([("ttype", "=", "reference")])
        )

        for record in records:
            try:
                Model = self.env[record.model]
                field = Model._fields[record.name]
            except KeyError:
                # unknown model or field => skip
                continue

            if Model._abstract or field.compute is not None:
                continue

            for partner in src_partners:
                records_ref = Model.sudo().search(
                    [(record.name, "=", "res.partner,%d" % partner.id)]
                )
                values = {
                    record.name: "res.partner,%d" % dst_partner.id,
                }
                records_ref.sudo().write(values)

        self.flush()