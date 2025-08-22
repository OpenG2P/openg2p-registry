import logging

from odoo import SUPERUSER_ID, api, fields

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if version == "17.0.1.3.0":
        _logger.info(f"Pre-Migration started for version {version}")

        # Step 1: Migrate pending reference_id records to new queue system
        model_record = env["ir.model"].search([("model", "=", "g2p.pending.reference_id")])
        if model_record:
            cr.execute(
                """
                    SELECT id, registrant_id
                    FROM g2p_pending_reference_id
                    WHERE status = 'failed'
                    AND registrant_id IS NOT NULL;

                """
            )
            pending_records = cr.fetchall()

            tasks_to_create = []
            for _, registrant_id in pending_records:
                tasks_to_create.append(
                    {
                        "worker_type": "id_generation_request_worker",
                        "worker_payload": {"registrant_id": registrant_id},
                        "task_status": "PENDING",
                        "number_of_attempts": 0,
                        "queued_datetime": fields.Datetime.now(),
                    }
                )
            if "g2p.que.background.task" in env.registry.models and tasks_to_create:
                env["g2p.que.background.task"].create(tasks_to_create)

        # Step 2: Add temp_unique_id column if not exists
        cr.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'res_partner'
            AND column_name = 'temp_unique_id'
        """
        )
        if not cr.fetchone()[0]:
            cr.execute("ALTER TABLE res_partner ADD COLUMN temp_unique_id VARCHAR;")

        # Step 3: Copy ref_id to temp_unique_id only if ref_id exists
        cr.execute(
            """
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name = 'res_partner' AND column_name = 'ref_id'
            """
        )
        if cr.fetchone()[0] > 0:
            cr.execute("UPDATE res_partner SET temp_unique_id = ref_id WHERE ref_id IS NOT NULL")

        _logger.info(f"Pre-Migration completed successfully for version {version}")
