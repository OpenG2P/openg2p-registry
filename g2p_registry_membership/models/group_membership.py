# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2PGroupMembership(models.Model):
    _name = "g2p.group.membership"
    _description = "Group Membership"
    _order = "id desc"

    group = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_group", "=", True), ("is_registrant", "=", True)],
        auto_join=True,
    )
    individual = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_group", "=", False), ("is_registrant", "=", True)],
        auto_join=True,
    )
    kind = fields.Many2many("g2p.group.membership.kind")
    start_date = fields.Datetime(default=lambda self: fields.Datetime.now())
    ended_date = fields.Datetime()
    individual_birthdate = fields.Date(related="individual.birthdate")
    individual_gender = fields.Selection(related="individual.gender")

    @api.onchange("kind")
    def _kind_onchange(self):
        for rec in self:
            origin_length = len(rec._origin.kind.ids)
            new_length = len(rec.kind.ids)
            if new_length > origin_length:
                unique_kinds = self.env["g2p.group.membership.kind"].search(
                    [("is_unique", "=", True)]
                )
                # Loop on all unique kinds
                for unique_kind_id in unique_kinds:
                    unique_count = 0

                    # Loop on group memberships
                    for line in rec.group.group_membership_ids:
                        # Get the id of group_membership then convert to string
                        members_id = str(line.id)
                        members_str = ""

                        # For editing the kind with newly added member,
                        # this will ignore the id with 0x as for newly added member has 2 ids
                        # (1st is the virtual id of the member, 2nd is unique identifier).
                        # This is used to not loop 2 times.

                        if members_id.find("0x") < 0:
                            for m in members_id:
                                # Only get the digit part of the string member id
                                # Newly added members has Neworigin prefix so this is used to remove that
                                if m.isdigit():
                                    members_str = members_str + m

                        # Loop only if the member_str is a digit
                        if members_str.isdigit():
                            for rec_line in line.kind:
                                # Get the id of kind then convert to string
                                kind_id = str(rec_line.id)
                                kind_str = ""

                                for m in kind_id:
                                    if m.isdigit():
                                        # Only get the digit part of the string kind id
                                        # Newly added kinds has Neworigin prefix so this is used to remove that
                                        kind_str = kind_str + m

                                # If the rec_line which is the kind id is the same with the unique kind
                                # then add unique count
                                if rec_line.id == unique_kind_id.id or kind_str == str(
                                    unique_kind_id.id
                                ):
                                    unique_count += 1

                    # This will check if the unique count from the loop is greater than 1
                    if unique_count > 1:
                        raise ValidationError(
                            _("Only one %s is allowed per group") % unique_kind_id.name
                        )

    @api.constrains("individual")
    def _check_group_members(self):
        for rec in self:
            rec_count = 0
            for group_membership_id in rec.group.group_membership_ids:
                if rec.individual.id == group_membership_id.individual.id:
                    rec_count += 1
            if rec_count > 1:
                raise ValidationError(_("Duplication of Member is not allowed "))

    def name_get(self):
        res = super(G2PGroupMembership, self).name_get()
        for rec in self:
            name = "NONE"
            if rec.group:
                name = rec.group.name
            res.append((rec.id, name))
        return res

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        if name:
            args = [("group", operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

    def _recompute_parent_groups(self, records):
        # Check if group field is in records
        if "group" in records._fields:
            field = self.env["res.partner"]._fields["force_recompute_canary"]
            groups = records.mapped("group")
            self.env.add_to_compute(field, groups)

    def write(self, vals):
        res = super(G2PGroupMembership, self).write(vals)
        self._recompute_parent_groups(self)
        return res

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        res = super(G2PGroupMembership, self).create(vals_list)
        self._recompute_parent_groups(res)
        return res

    def unlink(self):
        groups = self.mapped("group")
        res = super(G2PGroupMembership, self).unlink()
        self._recompute_parent_groups(groups)
        return res

    def open_individual_form(self):
        return {
            "name": "Individual Member",
            "view_mode": "form",
            "res_model": "res.partner",
            "res_id": self.individual.id,
            "view_id": self.env.ref("g2p_registry_individual.view_individuals_form").id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {"default_is_group": False},
            "flags": {"mode": "readonly"},
        }

    def open_group_form(self):
        return {
            "name": "Group Membership",
            "view_mode": "form",
            "res_model": "res.partner",
            "res_id": self.group.id,
            "view_id": self.env.ref("g2p_registry_group.view_groups_form").id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {"default_is_group": True},
            "flags": {"mode": "readonly"},
        }


class G2PGroupMembershipKind(models.Model):
    _name = "g2p.group.membership.kind"
    _description = "Group Membership Kind"
    _order = "id desc"

    name = fields.Char("Kind")
    is_unique = fields.Boolean("Unique")

    def unlink(self):
        for rec in self:
            external_identifier = self.env["ir.model.data"].search(
                [("res_id", "=", rec.id), ("model", "=", "g2p.group.membership.kind")]
            )
            if external_identifier.name in self._get_protected_external_identifier():
                raise ValidationError(_("Can't delete default kinds"))
            else:
                return super(G2PGroupMembershipKind, self).unlink()

    def _get_protected_external_identifier(self):
        return [
            "group_membership_kind_head",
        ]

    def write(self, vals):
        external_identifier = self.env["ir.model.data"].search(
            [("res_id", "=", self.id), ("model", "=", "g2p.group.membership.kind")]
        )
        if external_identifier.name in self._get_protected_external_identifier():
            raise ValidationError(_("Can't edit default kinds"))
        else:
            return super(G2PGroupMembershipKind, self).write(vals)
