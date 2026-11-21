import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Prepare unique(instance_id) and fix existing ODK pull crons to use hours."""
    _logger.info("Pre-migration 17.0.1.6.1 for g2p_odk_importer started")

    # Drop duplicate odk.instance.id rows, keeping the newest id per instance_id
    cr.execute(
        """
        DELETE FROM odk_instance_id
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (PARTITION BY instance_id ORDER BY id DESC) AS rn
                FROM odk_instance_id
            ) ranked
            WHERE rn > 1
        )
        """
    )
    _logger.info("Removed duplicate odk_instance_id rows: %s", cr.rowcount)

    # Fix active ODK pull crons that were created with interval_type=minutes.
    # Odoo 17 stores the label as cron_name (name lives on ir.actions.server).
    cr.execute(
        """
        UPDATE ir_cron
        SET interval_type = 'hours'
        WHERE cron_name LIKE 'ODK Pull Cron %'
          AND interval_type = 'minutes'
        """
    )
    _logger.info("Updated ODK Pull Cron interval_type to hours: %s", cr.rowcount)

    _logger.info("Pre-migration 17.0.1.6.1 for g2p_odk_importer completed")
