# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class G2PMembershipIndividual(models.Model):
    _inherit = "res.partner"

    individual_membership_ids = fields.One2many(
        "g2p.group.membership", "individual", "Membership to Groups"
    )

    def _recompute_parent_groups(self, records):
        field = self.env["res.partner"]._fields["force_recompute_canary"]
        for line in records:
            if line.is_registrant and not line.is_group:
                groups = line.individual_membership_ids.mapped("group")
                self.env.add_to_compute(field, groups)

    def write(self, vals):
        res = super(G2PMembershipIndividual, self).write(vals)
        self._recompute_parent_groups(self)
        return res

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        res = super(G2PMembershipIndividual, self).create(vals_list)
        self._recompute_parent_groups(res)
        return res
