# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class G2PWebSubBatchPublish(models.Model):
    _name = "g2p.websub.batch.publish"
    _description = "WebSub Batch Publish"
    _order = "create_date desc"

    sequence = fields.Integer(default=1)
    sequence_display = fields.Char(compute="_compute_sequence_display", store=True)
    config_id = fields.Many2one("g2p.datashare.config.websub", "WebSub Config", required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
    )

    # Progress tracking
    total_records = fields.Integer(default=0)
    processed_records = fields.Integer(default=0)
    successful_records = fields.Integer(default=0)
    failed_records = fields.Integer(default=0)
    skipped_records = fields.Integer(default=0)

    # Progress percentage
    progress_percentage = fields.Float("Progress %", compute="_compute_progress", store=True)

    # Batch settings
    batch_size = fields.Integer(default=100, required=True)
    partner_domain = fields.Text(help="Domain to filter partners for publishing")

    # Results
    result_message = fields.Text()
    error_log = fields.Text()

    # Timestamps
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    duration = fields.Char(compute="_compute_duration", store=True)

    @api.depends("sequence")
    def _compute_sequence_display(self):
        for record in self:
            record.sequence_display = f"P{record.sequence:08d}"

    @api.depends("processed_records", "total_records")
    def _compute_progress(self):
        for record in self:
            if record.total_records > 0:
                record.progress_percentage = (record.processed_records / record.total_records) * 100
            else:
                record.progress_percentage = 0.0

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                hours, remainder = divmod(delta.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                record.duration = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            else:
                record.duration = ""

    def action_start_batch_publish(self):
        """Start the batch publishing process"""
        self.ensure_one()

        if self.state != "draft":
            raise UserError(_("Only draft batches can be started."))

        # Get total count of partners to process
        domain = self._get_partner_domain()
        total_count = self.env["res.partner"].search_count(domain)

        if total_count == 0:
            raise UserError(_("No partners found matching the criteria."))

        # Update batch info
        self.write(
            {
                "total_records": total_count,
                "state": "running",
                "start_time": fields.Datetime.now(),
                "result_message": f"Starting batch publish for {total_count} partners...",
            }
        )

        _logger.info(
            "Starting WebSub batch publish - Config: %s, Total records: %s, Batch size: %s",
            self.config_id.name,
            total_count,
            self.batch_size,
        )

        # Start the batch processing job
        self.with_delay()._process_batch_publish()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Batch Publish Started"),
                "message": _("Batch publishing has started. Check the batch record for progress."),
                "sticky": True,
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _get_partner_domain(self):
        """Get the domain for partners to process"""
        base_domain = [("is_registrant", "=", True)]

        if self.partner_domain:
            try:
                import ast

                custom_domain = ast.literal_eval(self.partner_domain)
                if isinstance(custom_domain, list):
                    base_domain.extend(custom_domain)
            except (ValueError, SyntaxError):
                _logger.warning("Invalid partner domain: %s", self.partner_domain)

        return base_domain

    def _process_batch_publish(self):
        """Process the batch publishing using job queue"""
        self.ensure_one()

        try:
            domain = self._get_partner_domain()
            partners = self.env["res.partner"].search(domain, order="id")

            _logger.info(
                "Processing WebSub batch publish - Config: %s, Partners: %s",
                self.config_id.name,
                len(partners),
            )

            # Track job completion
            total_batches = (len(partners) - 1) // self.batch_size + 1

            # Process partners in batches
            for i in range(0, len(partners), self.batch_size):
                batch_partners = partners[i : i + self.batch_size]
                batch_number = i // self.batch_size + 1

                # Create a job for this batch with callback
                self.with_delay()._process_partner_batch(batch_partners.ids, batch_number, total_batches)

                # Update progress
                self.write(
                    {
                        "processed_records": min(i + self.batch_size, len(partners)),
                        "result_message": f"Processing batch {batch_number} of {total_batches}",
                    }
                )

            _logger.info(
                "WebSub batch publish jobs created - Config: %s, Total batches: %s",
                self.config_id.name,
                total_batches,
            )

        except Exception as e:
            _logger.error("WebSub batch publish failed - Config: %s, Error: %s", self.config_id.name, str(e))

            self.write(
                {
                    "state": "failed",
                    "end_time": fields.Datetime.now(),
                    "error_log": str(e),
                    "result_message": f"Batch publish failed: {str(e)}",
                }
            )

    def _process_partner_batch(self, partner_ids, batch_number, total_batches):
        """Process a batch of partners"""
        self.ensure_one()

        try:
            partners = self.env["res.partner"].browse(partner_ids)

            for partner in partners:
                try:
                    # Publish the partner
                    self.config_id.publish_by_publisher({"id": partner.id}, condition_override="true")

                    # Update success count
                    self.write({"successful_records": self.successful_records + 1})

                    _logger.debug("WebSub batch publish - Successfully published partner ID: %s", partner.id)

                except Exception as e:
                    # Update failure count
                    self.write({"failed_records": self.failed_records + 1})

                    _logger.error(
                        "WebSub batch publish - Failed to publish partner ID: %s, Error: %s",
                        partner.id,
                        str(e),
                    )

            # Check if this was the last batch
            self._check_batch_completion(batch_number, total_batches)

        except Exception as e:
            _logger.error("WebSub batch publish - Batch processing failed: %s", str(e))
            # Mark as failed if batch processing fails
            self.write(
                {
                    "state": "failed",
                    "end_time": fields.Datetime.now(),
                    "error_log": str(e),
                    "result_message": f"Batch processing failed: {str(e)}",
                }
            )

    def _check_batch_completion(self, batch_number, total_batches):
        """Check if all batches are completed and update status accordingly"""
        self.ensure_one()

        # Update processed records count
        self.write({"processed_records": min(batch_number * self.batch_size, self.total_records)})

        if batch_number >= total_batches:
            # All batches completed
            self.write(
                {
                    "state": "completed",
                    "end_time": fields.Datetime.now(),
                    "result_message": f"Completed. Processed {self.processed_records} partners."
                    f"Successful: {self.successful_records}, Failed: {self.failed_records}",
                }
            )

            _logger.info(
                "WebSub batch publish completed - Config: %s, Processed: %s, Successful: %s, Failed: %s",
                self.config_id.name,
                self.processed_records,
                self.successful_records,
                self.failed_records,
            )

    def action_cancel_batch(self):
        """Cancel the batch publishing"""
        self.ensure_one()

        if self.state in ["completed", "failed", "cancelled"]:
            raise UserError(_("Cannot cancel a batch that is already finished."))

        # Note: We can't actually cancel running jobs in the queue,
        # but we can mark the batch as cancelled to prevent further processing
        self.write(
            {
                "state": "cancelled",
                "end_time": fields.Datetime.now(),
                "result_message": f"Processed {self.processed_records} partners before cancellation.",
            }
        )

        _logger.info(
            "WebSub batch publish cancelled - Config: %s, Processed: %s",
            self.config_id.name,
            self.processed_records,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Batch Cancelled"),
                "message": _("Cancelled. Note: Jobs already in queue will continue processing."),
                "sticky": True,
                "type": "warning",
            },
        }

    def action_view_partners(self):
        """View the partners that would be processed"""
        self.ensure_one()

        domain = self._get_partner_domain()

        return {
            "name": _("Partners to Publish"),
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": domain,
            "context": {"search_default_is_registrant": 1},
        }
