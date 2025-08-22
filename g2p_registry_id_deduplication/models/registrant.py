# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_duplicated = fields.Boolean(default=False)

    def deduplicate_registrants(self):
        is_group = self._context.get("default_is_group")
        self.reset_duplicate_flag(is_group)

        if not is_group:
            ind_id_types = self.get_id_types_with_kind(
                id_field="ind_deduplication_id_types_ids", is_group=is_group
            )
            ind_duplicate_ids = []
            duplicates = self.get_duplicate_registrants(
                is_group, ind_id_types[False], group_condition="group_kind.name IS NULL"
            )

            for duplicate in duplicates:
                ind_duplicate_ids += duplicate.get("partner_ids").split(",")

            updated_ind_duplicate_ids = list(set(ind_duplicate_ids))
            self.mark_registrant_as_duplicated(updated_ind_duplicate_ids)

            message = f"{len(updated_ind_duplicate_ids)} individuals"

        else:
            grp_id_types = self.get_id_types_with_kind(
                id_field="grp_deduplication_id_types_ids", is_group=is_group
            )
            group_duplicate_ids = []
            member_grp_duplicate_ids = []
            member_individual_ids = []
            grouped_kinds = self.get_grouped_kinds()
            updated_grp_duplicate_ids = []
            updated_member_grp_duplicate_ids = []
            for kind in grouped_kinds:
                group_kind_name = kind.get("kind")
                group_ids_str = kind.get("group_ids")

                group_duplicates = []
                if group_kind_name in grp_id_types or (group_kind_name is None and "False" in grp_id_types):
                    group_duplicates = self.get_duplicate_registrants(
                        is_group,
                        grp_id_types["False" if group_kind_name is None else group_kind_name],
                        group_condition=(
                            f"group_kind.name = '{group_kind_name}'"
                            if group_kind_name is not None
                            else "group_kind.name IS NULL"
                        ),
                    )

                # Group Duplicate
                for duplicate in group_duplicates:
                    group_duplicate_ids += duplicate.get("partner_ids").split(",")

                updated_grp_duplicate_ids = list(set(group_duplicate_ids))
                self.mark_registrant_as_duplicated(updated_grp_duplicate_ids)

                # Group Member Duplicate
                if group_kind_name in grp_id_types or (group_kind_name is None and "False" in grp_id_types):
                    group_member_duplicates = self.get_duplicate_group_members(
                        group_ids_str, grp_id_types["False" if group_kind_name is None else group_kind_name]
                    )
                    for member_duplicate in group_member_duplicates:
                        member_grp_duplicate_ids += member_duplicate.get("partner_ids").split(",")
                        member_individual_ids += member_duplicate.get("individual_ids").split(",")

                updated_member_grp_duplicate_ids = list(set(member_grp_duplicate_ids))
                updated_member_individual_ids = list(set(member_individual_ids))
                self.mark_registrant_as_duplicated(updated_member_grp_duplicate_ids)

            if len(updated_grp_duplicate_ids) > 0 and len(updated_member_individual_ids) > 0:
                message = f"{len(updated_grp_duplicate_ids)} groups and \
                    {len(updated_member_individual_ids)} group members"
            elif len(updated_member_individual_ids) > 0:
                message = f"{len(updated_member_individual_ids)} group members"
            else:
                message = f"{len(updated_grp_duplicate_ids)} groups"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Duplicate"),
                "message": f"{message} are duplicated.",
                "sticky": False,
                "type": "success",
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }

    def get_id_types_with_kind(self, id_field, is_group):
        id_types = {}

        ir_config = self.env["ir.config_parameter"].sudo()
        id_type_ids_str = ir_config.get_param(f"g2p_registry_id_deduplication.{id_field}", default=None)

        id_type_ids = safe_eval.safe_eval(id_type_ids_str)

        if len(id_type_ids) < 1:
            raise UserError(_("Deduplication is not configured"))

        ind_id_type = []
        for id_type in id_type_ids:
            if is_group and id_field == "grp_deduplication_id_types_ids":
                kind_id_type_mapping = (
                    self.env["g2p.group.kind.deduplication.config"]
                    .sudo()
                    .search([("id", "=", id_type)], limit=1)
                )
                id_types_mapping = []
                for rec in kind_id_type_mapping.id_type_ids:
                    id_types_mapping.append(rec.name)

                if len(id_types_mapping) < 1:
                    raise UserError(_("No Configured ID Types found in the System"))

                id_types.update(
                    {
                        f"{kind_id_type_mapping.kind_id.name}": tuple(id_types_mapping)
                        if len(id_types_mapping) != 1
                        else f"('{id_types_mapping[0]}')"
                    }
                )

            else:
                id_type_name = self.env["g2p.id.type"].sudo().search([("id", "=", id_type)], limit=1)
                ind_id_type.append(id_type_name.name)

        if id_field == "ind_deduplication_id_types_ids":
            id_types.update({False: tuple(ind_id_type) if len(ind_id_type) != 1 else f"('{ind_id_type[0]}')"})

        if len(id_types) < 1:
            raise UserError(_("No Configured ID Types found in the System"))

        return id_types

    def mark_registrant_as_duplicated(self, partner_ids):
        for partner in partner_ids:
            registrant = self.browse(int(partner))
            if registrant:
                registrant.update({"is_duplicated": True})

    def reset_duplicate_flag(self, is_group):
        query = f"""
            UPDATE res_partner
            SET is_duplicated = FALSE
            WHERE is_registrant = TRUE AND is_group = {is_group}
        """
        _logger.debug("DB Query: %s" % query)

        try:
            self._cr.execute(query)  # pylint: disable=sql-injection
        except Exception as e:
            _logger.error("Database Query Error: %s", e)
            raise UserError(_("Database Query Error: %s") % e) from None

    def get_grouped_kinds(self):
        query = """
            SELECT
            group_kind.name AS kind, STRING_AGG(partner.id::text, ',')
            AS group_ids
            FROM res_partner AS partner
            LEFT JOIN g2p_group_kind AS group_kind ON group_kind.id = partner.kind
            WHERE is_registrant = TRUE AND is_group = TRUE
            GROUP BY group_kind.name
        """

        try:
            self._cr.execute(query)  # pylint: disable=sql-injection
            grouped_kinds = self._cr.dictfetchall()
            return grouped_kinds
        except Exception as e:
            _logger.error("Database Query Error: %s", e)
            raise UserError(_("Database Query Error: %s") % e) from None

    def get_duplicate_registrants(self, is_group, id_types, group_condition):
        query = f"""
            SELECT
            id_type.name AS id_name, reg_id.value AS id_value, STRING_AGG(partner.id::text, ',')
            AS partner_ids
            FROM res_partner AS partner
            INNER JOIN g2p_reg_id AS reg_id ON reg_id.partner_id = partner.id
            JOIN g2p_id_type AS id_type ON id_type.id = reg_id.id_type
            LEFT JOIN g2p_group_kind AS group_kind ON group_kind.id = partner.kind
            WHERE is_registrant = TRUE AND id_type.name IN {id_types} AND is_group = {is_group}
            AND {group_condition}
            GROUP BY id_type.name, reg_id.value
            HAVING COUNT(partner.id) > 1
        """

        try:
            self._cr.execute(query)  # pylint: disable=sql-injection
            individual_duplicates = self._cr.dictfetchall()
            return individual_duplicates
        except Exception as e:
            _logger.error("Database Query Error: %s", e)
            raise UserError(_("Database Query Error: %s") % e) from None

    def get_duplicate_group_members(self, group_ids, id_types):
        query = f"""
            SELECT
            id_type.name AS id_name, reg_id.value AS id_value, STRING_AGG(group_member.group::text, ',')
            AS partner_ids, STRING_AGG(group_member.individual::text, ',') AS individual_ids
            FROM res_partner AS partner
            JOIN g2p_group_membership AS group_member ON partner.id = group_member.individual
            INNER JOIN g2p_reg_id AS reg_id ON reg_id.partner_id = partner.id
            JOIN g2p_id_type AS id_type ON id_type.id = reg_id.id_type
            WHERE partner.is_registrant = TRUE AND id_type.name IN {id_types}
            AND group_member.group IN ({group_ids})
            GROUP BY id_type.name, reg_id.value
            HAVING COUNT(partner.id) > 1
        """

        try:
            self._cr.execute(query)  # pylint: disable=sql-injection
            group_duplicates = self._cr.dictfetchall()
            return group_duplicates
        except Exception as e:
            _logger.error("Database Query Error: %s", e)
            raise UserError(_("Database Query Error: %s") % e) from None
