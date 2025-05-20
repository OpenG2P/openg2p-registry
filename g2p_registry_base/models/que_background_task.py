from odoo import fields, models


class G2PQueBackgroundTask(models.Model):
    _name = "g2p.que.background.task"
    _description = "G2P Queue Background Task"

    worker_type = fields.Char(default="example_worker")  # Default worker type
    worker_payload = fields.Json(required=True)
    task_status = fields.Selection(
        selection=[
            ("PENDING", "PENDING"),
            ("COMPLETED", "COMPLETED"),
            ("FAILED", "FAILED"),
        ],
        required=True,
        default="PENDING",
    )
    queued_datetime = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
    )
    number_of_attempts = fields.Integer(
        required=True,
        default=0,
    )
    last_attempt_datetime = fields.Datetime()
    last_attempt_error_code = fields.Char()
