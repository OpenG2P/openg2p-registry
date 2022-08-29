# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class G2PMembershipGroup(models.Model):
    _inherit = "res.partner"

    group_membership_ids = fields.One2many(
        "g2p.group.membership", "group", "Group Members"
    )

    def count_individuals(self, relationship_kinds=None, indicators=None):
        """
        Count the number of individuals in the group that match the kinds and indicators.
        """
        _logger.info("SQL DEBUG: count_individuals: records:%s" % self.ids)
        membership_kind_domain = None
        individual_domain = None
        if self.group_membership_ids:
            if relationship_kinds:
                membership_kind_domain = [("name", "in", relationship_kinds)]
        else:
            return 0

        if indicators is not None:
            individual_domain = indicators

        query_result = self._query_members_aggregate(
            membership_kind_domain, individual_domain
        )

        return query_result

    def _query_members_aggregate(
        self, membership_kind_domain=None, individual_domain=None
    ):
        _logger.info("SQL DEBUG: query_members_aggregate: records:%s" % self.ids)
        ids = self.ids
        partner_model = "res.partner"
        domain = [("is_registrant", "=", True), ("is_group", "=", True)]
        query_obj = self.env[partner_model]._where_calc(domain)

        membership_alias = query_obj.left_join(
            "res_partner", "id", "g2p_group_membership", "group", "id"
        )
        individual_alias = query_obj.left_join(
            membership_alias, "individual", "res_partner", "id", "individual"
        )
        membership_kind_rel_alias = query_obj.left_join(
            membership_alias,
            "id",
            "g2p_group_membership_g2p_group_membership_kind_rel",
            "g2p_group_membership_id",
            "id",
        )
        rel_kind_alias = query_obj.left_join(
            membership_kind_rel_alias,
            "g2p_group_membership_kind_id",
            "g2p_group_membership_kind",
            "id",
            "id",
        )

        # Build where clause for the membership_alias
        membership_query_obj = expression.expression(
            model=self.env["g2p.group.membership"],
            domain=[("end_date", "=", None), ("group", "in", ids)],
            alias=membership_alias,
        ).query
        (
            membership_from_clause,
            membership_where_clause,
            membership_where_params,
        ) = membership_query_obj.get_sql()
        # _logger.info("SQL DEBUG: Membership Kind Query: From:%s, Where:%s, Params:%s" %
        #   (membership_from_clause,membership_where_clause,membership_where_params))
        query_obj.add_where(membership_where_clause, membership_where_params)

        if membership_kind_domain:
            membership_kind_query_obj = expression.expression(
                model=self.env["g2p.group.membership.kind"],
                domain=membership_kind_domain,
                alias=rel_kind_alias,
            ).query
            (
                membership_kind_from_clause,
                membership_kind_where_clause,
                membership_kind_where_params,
            ) = membership_kind_query_obj.get_sql()
            # _logger.info("SQL DEBUG: Membership Kind Query: From:%s, Where:%s, Params:%s" %
            #   (membership_kind_from_clause,membership_kind_where_clause,membership_kind_where_params))
            query_obj.add_where(
                membership_kind_where_clause, membership_kind_where_params
            )

        if individual_domain:
            individual_query_obj = expression.expression(
                model=self.env[partner_model],
                domain=individual_domain,
                alias=individual_alias,
            ).query
            (
                individual_from_clause,
                individual_where_clause,
                individual_where_params,
            ) = individual_query_obj.get_sql()
            # _logger.info("SQL DEBUG: Individual Query: From:%s, Where:%s, Params:%s" %
            #   (individual_from_clause,individual_where_clause,individual_where_params))
            query_obj.add_where(individual_where_clause, individual_where_params)

        select_query, select_params = query_obj.select(
            "res_partner.id AS id", "count(*) AS members_cnt"
        )

        # In the absence of managing "GROUP BY" by Odoo Query object,
        # we will add the GROUP BY clause manually
        select_query += " GROUP BY " + partner_model.replace(".", "_") + ".id"
        _logger.info(
            "SQL DEBUG: SQL query: %s, params: %s" % (select_query, select_params)
        )

        self._cr.execute(select_query, select_params)
        # Generate result as dict
        # results = self._cr.dictfetchall()
        # Generate result as tuple
        results = self._cr.fetchall()
        _logger.info("SQL DEBUG: SQL Query Result: %s" % results)
        return results

    def compute_count_and_set_indicator(
        self, field_name, kinds, indicators, presence_only=False
    ):
        """
        This method is used to compute the count then set it.
        :param field_name: The Field Name.
        :param kinds: The Kinds.
        :param indicators: The indicators.
        :return: The count then set it on the Field Name.
        """

        _logger.info(
            "SQL DEBUG: compute_count_and_set_indicator: total records:%s" % len(self)
        )
        # Check if we need to use job_queue
        # Get groups only
        records = self.filtered(lambda a: a.is_group)
        tot_rec = len(records)
        max_rec = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry.max_registrants_count_job_queue")
        )
        try:
            max_rec = int(max_rec)
        except Exception:
            max_rec = 200
        if tot_rec <= max_rec:
            query_result = None
            if records:
                # Generate the SQL query
                query_result = records.count_individuals(
                    relationship_kinds=kinds, indicators=indicators
                )
                _logger.info(
                    "SQL DEBUG: compute_count_and_set_indicator: field:%s, results:%s"
                    % (field_name, query_result)
                )
                if query_result:
                    # Update the compute fields and affected records
                    query_result = ", ".join(map(str, query_result))
                    update_params = (field_name, query_result)
                    if not presence_only:
                        update_sql = (
                            """
                            UPDATE res_partner AS p
                                SET %s = r.members_cnt
                            FROM (VALUES
                                %s
                            ) AS r(id, members_cnt)
                            where r.id = p.id
                        """
                            % update_params
                        )
                    else:
                        update_sql = (
                            """
                            UPDATE res_partner AS p
                                SET %s =
                                    CASE WHEN r.members_cnt > 0 THEN
                                        True
                                    ELSE
                                        False
                                    END
                            FROM (VALUES
                                %s
                            ) AS r(id, members_cnt)
                            where r.id = p.id
                        """
                            % update_params
                        )

                    _logger.info(
                        "SQL DEBUG: compute_count_and_set_indicator: update_sql:%s, update_params:%s"
                        % (update_sql, update_params)
                    )
                    self._cr.execute(update_sql, ())

        else:
            # Update compute fields in batch using job_queue
            batch_cnt = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("g2p_registry.batch_registrants_count_job_queue")
            )
            try:
                batch_cnt = int(batch_cnt)
            except Exception:
                batch_cnt = 2000

            # Todo: Divide recordset (self) to batches by batch_cnt
            # Run using Job Queue
            self.with_delay()._update_compute_fields(
                self, field_name, kinds, indicators, presence_only=presence_only
            )

            # # Send message to admins via odoobot
            # message = _(
            #     "The processing of the calculated field: %(field)s with %(cnt)s records "
            #     + "was put on queue. You will be notified once the process is completed."
            # ) % {"field": field_name, "cnt": tot_rec}
            # self._send_message_admins(message)

    def _update_compute_fields(
        self, records, field_name, kinds, indicators, presence_only=False
    ):
        # Get groups only
        records = records.filtered(lambda a: a.is_group)

        query_result = None
        if records:
            # Generate the SQL query using Job Queue
            query_result = records.count_individuals(
                relationship_kinds=kinds, indicators=indicators
            )
            _logger.info(
                "SQL DEBUG: job_queue->_update_compute_fields: field:%s, results:%s"
                % (field_name, query_result)
            )
            if query_result:
                # Update the compute fields and affected records
                query_result = ", ".join(map(str, query_result))
                update_params = (field_name, query_result)
                if not presence_only:
                    update_sql = (
                        """
                        UPDATE res_partner AS p
                            SET %s = r.members_cnt
                        FROM (VALUES
                            %s
                        ) AS r(id, members_cnt)
                        where r.id = p.id
                    """
                        % update_params
                    )
                else:
                    update_sql = (
                        """
                        UPDATE res_partner AS p
                            SET %s =
                                CASE WHEN r.members_cnt > 0 THEN
                                    True
                                ELSE
                                    False
                                END
                        FROM (VALUES
                            %s
                        ) AS r(id, members_cnt)
                        where r.id = p.id
                    """
                        % update_params
                    )

                _logger.info(
                    "SQL DEBUG: job_queue->_update_compute_fields: update_sql:%s, update_params:%s"
                    % (update_sql, update_params)
                )
                self._cr.execute(update_sql, ())

            # # Send message to admins via odoobot
            # message = _("All compute fields are updated.")
            # self._send_message_admins(message)

    #
    # def _send_message_admins(self, message):
    #     """Adopt OdooBot Send a message to group g2p_registry_base.group_g2p_admin users
    #
    #     :param user: 'res.users'  object
    #     :param message: str,  The message content
    #     """
    #     # Obtain the OdooBot ID
    #     odoobot_id = self.env["ir.model.data"]._xmlid_to_res_id("base.partner_root")
    #
    #     # Obtain OdooBot Chat channels of g2p_registry_base.group_g2p_admin users
    #     admin_group_id = self.env["ir.model.data"]._xmlid_to_res_id(
    #         "g2p_registry_base.group_g2p_admin"
    #     )
    #     admin_group = (
    #         self.env["res.groups"].sudo().search([("id", "=", admin_group_id)])
    #     )
    #     channel_users = admin_group.mapped("users")
    #
    #     for user in channel_users:
    #         channel = (
    #             self.env["mail.channel"]
    #             .sudo()
    #             .search(
    #                 [
    #                     ("channel_type", "=", "chat"),
    #                     ("channel_partner_ids", "in", [user.partner_id.id]),
    #                     ("channel_partner_ids", "in", [odoobot_id]),
    #                 ],
    #                 limit=1,
    #             )
    #         )
    #
    #         #  If it does not exist, initialize the chat channel
    #         if not channel:
    #             user.odoobot_state = "not_initialized"
    #             channel = self.env["mail.channel"].with_user(user).init_odoobot()
    #         #  Send a message
    #         channel.sudo().message_post(
    #             body=message,
    #             author_id=odoobot_id,
    #             message_type="comment",
    #             subtype_xmlid="mail.mt_comment",
    #         )
