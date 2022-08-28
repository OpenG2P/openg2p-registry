# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class G2PRegistry(models.Model):
    _inherit = "res.partner"

    # Custom Fields
    address = fields.Text("Address")
    disabled = fields.Datetime("Date Disabled")
    disabled_reason = fields.Text("Reason for disabling")
    disabled_by = fields.Many2one("res.users", "Disabled by")

    reg_ids = fields.One2many("g2p.reg.id", "partner_id", "Registrant IDs")
    is_registrant = fields.Boolean("Registrant")
    is_group = fields.Boolean("Group")

    name = fields.Char(index=True, translate=True)

    related_1_ids = fields.One2many(
        "g2p.reg.rel", "registrant2", "Related to registrant 1"
    )
    related_2_ids = fields.One2many(
        "g2p.reg.rel", "registrant1", "Related to registrant 2"
    )

    phone_number_ids = fields.One2many(
        "g2p.phone.number", "partner_id", "Phone Numbers"
    )

    registration_date = fields.Date("Registration Date")

    last_update = fields.Datetime()

    @api.onchange("phone_number_ids")
    def phone_number_ids_change(self):
        phone = ""
        if self.phone_number_ids:
            phone = ",".join(
                [
                    p
                    for p in self.phone_number_ids.filtered(
                        lambda rec: not rec.disabled
                    ).mapped("phone_no")
                ]
            )
        self.phone = phone

    def enable_registrant(self):
        for rec in self:
            if rec.disabled:
                rec.update(
                    {
                        "disabled": None,
                        "disabled_by": None,
                        "disabled_reason": None,
                    }
                )

    def _compute_count_and_set(self, field_name, kinds, indicators):
        """
        This method is used to compute the count then set it.
        :param field_name: The Field Name.
        :param kinds: The Kinds.
        :param indicators: The indicatorss.
        :return: The count then set it on the Field Name.
        """

        _logger.info("SQL DEBUG: _compute_count_and_set: total records:%s" % len(self))
        # Check if we need to use job_queue
        tot_rec = len(self)
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
            # Get groups only
            records = self.filtered(lambda a: a.is_group)
            query_result = None
            if records:
                # Generate the SQL query
                query_result = records.count_individuals(
                    kinds=kinds, indicators=indicators
                )
                _logger.info(
                    "SQL DEBUG: _compute_count_and_set: field:%s, results:%s"
                    % (field_name, query_result)
                )
                if query_result:
                    # Update the compute fields and affected records
                    for res in query_result:
                        update_sql = (
                            "UPDATE res_partner SET " + field_name + " = %s WHERE id=%s"
                        )
                        update_params = (res["members_cnt"], res["id"])
                        self._cr.execute(update_sql, update_params)
                        _logger.info(
                            "SQL DEBUG: _compute_count_and_set: update_sql:%s, update_params:%s"
                            % (update_sql, update_params)
                        )

                    # for record in records:
                    #    rec = next(
                    #        (
                    #            item
                    #            for item in query_result
                    #            if item["id"] == record["id"]
                    #        ),
                    #        None,
                    #    )
                    #    if rec:
                    #        record[field_name] = rec["members_cnt"]
                    #        _logger.info(
                    #            "SQL DEBUG: _compute_count_and_set: members_cnt:%s"
                    #            % rec["members_cnt"]
                    #        )
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
                self, field_name, kinds, indicators
            )

            # Send message to admins via odoobot
            message = _(
                "The processing of the calculated field: %(field)s with %(cnt)s records "
                + "was put on queue. You will be notified once the process is completed."
            ) % {"field": field_name, "cnt": tot_rec}
            self._send_message_admins(message)

    def _send_message_admins(self, message):
        """Adopt OdooBot Send a message to group g2p_registry_base.group_g2p_admin users

        :param user: 'res.users'  object
        :param message: str,  The message content
        """
        # Obtain the OdooBot ID
        odoobot_id = self.env["ir.model.data"]._xmlid_to_res_id("base.partner_root")

        # Obtain OdooBot Chat channels of g2p_registry_base.group_g2p_admin users
        admin_group_id = self.env["ir.model.data"]._xmlid_to_res_id(
            "g2p_registry_base.group_g2p_admin"
        )
        admin_group = (
            self.env["res.groups"].sudo().search([("id", "=", admin_group_id)])
        )
        channel_users = admin_group.mapped("users")

        for user in channel_users:
            channel = (
                self.env["mail.channel"]
                .sudo()
                .search(
                    [
                        ("channel_type", "=", "chat"),
                        ("channel_partner_ids", "in", [user.partner_id.id]),
                        ("channel_partner_ids", "in", [odoobot_id]),
                    ],
                    limit=1,
                )
            )

            #  If it does not exist, initialize the chat channel
            if not channel:
                user.odoobot_state = "not_initialized"
                channel = self.env["mail.channel"].with_user(user).init_odoobot()
            #  Send a message
            channel.sudo().message_post(
                body=message,
                author_id=odoobot_id,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

    def _update_compute_fields(self, records, field_name, kinds, indicators):
        # Get groups only
        records = records.filtered(lambda a: a.is_group)

        query_result = None
        if records:
            # Generate the SQL query using Job Queue
            query_result = records.count_individuals(kinds=kinds, indicators=indicators)
            _logger.info(
                "SQL DEBUG: job_queue->_update_compute_fields: field:%s, results:%s"
                % (field_name, query_result)
            )
            if query_result:
                for res in query_result:
                    update_sql = (
                        "UPDATE res_partner SET " + field_name + " = %s WHERE id=%s"
                    )
                    update_params = (res["members_cnt"], res["id"])
                    self._cr.execute(update_sql, update_params)
                    _logger.info(
                        "SQL DEBUG: job_queue->_update_compute_fields: update_sql:%s, update_params:%s"
                        % (update_sql, update_params)
                    )

                # Update the compute fields and affected records
                # for record in records:
                #    rec = next(
                #        (item for item in query_result if item["id"] == record["id"]),
                #        None,
                #    )
                #    if rec:
                #        record[field_name] = rec["members_cnt"]
                #        _logger.info(
                #            "SQL DEBUG: job_queue->_update_compute_fields: members_cnt:%s"
                #            % rec["members_cnt"]
                #        )

            # Send message to admins via odoobot
            message = _("All compute fields are updated.")
            self._send_message_admins(message)
