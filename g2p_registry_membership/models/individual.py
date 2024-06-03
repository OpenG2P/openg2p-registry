# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2PMembershipIndividual(models.Model):
    _inherit = "res.partner"  # pylint: disable=[R8180]

    individual_membership_ids = fields.One2many("g2p.group.membership", "individual", "Membership to Groups")

    def _recompute_parent_groups(self, records):
        field = self.env["res.partner"]._fields["force_recompute_canary"]
        for line in records:
            if line.is_registrant and not line.is_group:
                try:
                    groups = line.individual_membership_ids.mapped("group")
                    for group in groups:
                        unique_kinds = group.env["g2p.group.membership.kind"].search(
                            [("is_unique", "=", True)]
                        )
                        for unique_kind in unique_kinds:
                            count = sum(
                                1 for rec in group.group_membership_ids if unique_kind.id in rec.kind.ids
                            )
                            if count > 1:
                                raise ValidationError(
                                    _("Only one %s is allowed per group") % unique_kind.name
                                )
                except Exception as e:
                    _logger.error("_recompute_parent_groups: exception: %s", e)
                    raise
                else:
                    self.env.add_to_compute(field, groups)

    def write(self, vals):
        res = super().write(vals)
        self._recompute_parent_groups(self)
        return res

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        res = super().create(vals_list)
        self._recompute_parent_groups(res)
        return res
