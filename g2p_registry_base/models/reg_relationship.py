# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class G2PRegistrantRelationship(models.Model):
    _name = "g2p.reg.rel"
    _description = "Registrant Relationship"
    _order = "id desc"
    _inherit = ["mail.thread"]

    source = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_registrant", "=", True)],
    )
    destination = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_registrant", "=", True)],
    )
    relation = fields.Many2one("g2p.relationship")
    disabled = fields.Datetime("Date Disabled")
    disabled_by = fields.Many2one("res.users")
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    relation_as_str = fields.Char(related="relation.name")

    @api.constrains("source", "destination")
    def _check_registrants(self):
        for rec in self:
            if rec.source == rec.destination:
                raise ValidationError(
                    _("Registrant 1 and Registrant 2 cannot be the same.")
                )

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for record in self:
            if (
                record.start_date
                and record.end_date
                and record.start_date > record.end_date
            ):
                raise ValidationError(
                    _("The starting date cannot be after the ending date.")
                )

    @api.constrains("source", "relation", "destination", "start_date", "end_date")
    def _check_relation_uniqueness(self):
        """Forbid multiple active relations of the same type between the same
        partners
        :raises ValidationError: When constraint is violated
        """
        # pylint: disable=no-member
        # pylint: disable=no-value-for-parameter
        for record in self:
            domain = [
                ("relation", "=", record.relation.id),
                ("id", "!=", record.id),
                ("source", "=", record.source.id),
                ("destination", "=", record.destination.id),
            ]
            if record.start_date:
                domain += [
                    "|",
                    ("end_date", "=", False),
                    ("end_date", ">=", record.start_date),
                ]
            if record.end_date:
                domain += [
                    "|",
                    ("start_date", "=", False),
                    ("start_date", "<=", record.end_date),
                ]
            if record.search(domain):
                raise ValidationError(
                    _("There is already a similar relation with " "overlapping dates")
                )

    @api.constrains("source", "relation")
    def _check_source(self):
        self._check_partner("source")

    @api.constrains("destination", "relation")
    def _check_destination(self):
        self._check_partner("destination")

    def _check_partner(self, side):
        for record in self:
            assert side in ["source", "destination"]
            ptype = getattr(record.relation, "%s_type" % side)
            partner = getattr(record, "%s" % side)
            if (
                not partner.is_registrant
                or (ptype == "i" and partner.is_group)
                or (ptype == "g" and not partner.is_group)
            ):
                raise ValidationError(
                    _("This registrant is not applicable for this " "relation type.")
                )

    def name_get(self):
        res = super(G2PRegistrantRelationship, self).name_get()
        for rec in self:
            name = ""
            if rec.source:
                name += rec.source.name
            if rec.destination:
                name += " / " + rec.destination.name
            res.append((rec.id, name))
        return res

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        if name:
            args = [
                "|",
                ("source", operator, name),
                ("destination", operator, name),
            ] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

    def disable_relationship(self):
        for rec in self:
            if not rec.disabled:
                rec.update(
                    {
                        "disabled": fields.Datetime.now(),
                        "disabled_by": self.env.user,
                    }
                )

    def enable_relationship(self):
        for rec in self:
            if rec.disabled:
                rec.update(
                    {
                        "disabled": None,
                        "disabled_by": None,
                    }
                )

    def open_relationship1_form(self):
        if self.source.is_group:
            return {
                "name": "Related Group",
                "view_mode": "form",
                "res_model": "res.partner",
                "res_id": self.source.id,
                "view_id": self.env.ref("g2p_registry_group.view_groups_form").id,
                "type": "ir.actions.act_window",
                "target": "new",
            }
        else:
            return {
                "name": "Related Registrant",
                "view_mode": "form",
                "res_model": "res.partner",
                "res_id": self.source.id,
                "view_id": self.env.ref(
                    "g2p_registry_individual.view_individuals_form"
                ).id,
                "type": "ir.actions.act_window",
                "target": "new",
            }

    def open_relationship2_form(self):
        if self.destination.is_group:
            return {
                "name": "Other Related Group",
                "view_mode": "form",
                "res_model": "res.partner",
                "res_id": self.destination.id,
                "view_id": self.env.ref("g2p_registry_group.view_groups_form").id,
                "type": "ir.actions.act_window",
                "target": "new",
            }
        else:
            return {
                "name": "Other Related Registrant",
                "view_mode": "form",
                "res_model": "res.partner",
                "res_id": self.destination.id,
                "view_id": self.env.ref(
                    "g2p_registry_individual.view_individuals_form"
                ).id,
                "type": "ir.actions.act_window",
                "target": "new",
            }


class G2PRelationship(models.Model):
    _name = "g2p.relationship"
    _description = "Relationship"
    _order = "id desc"

    name = fields.Char(translate=True)
    name_inverse = fields.Char(string="Inverse name", required=True, translate=True)
    bidirectional = fields.Boolean("Bi-directional", default=False)
    source_type = fields.Selection(
        selection="get_partner_types", string="Source partner type"
    )
    destination_type = fields.Selection(
        selection="get_partner_types", string="Destination partner type"
    )

    @api.model
    def get_partner_types(self):
        """A partner can be an organisation or an individual."""
        # pylint: disable=no-self-use
        return [("g", _("Group")), ("i", _("Individual"))]
