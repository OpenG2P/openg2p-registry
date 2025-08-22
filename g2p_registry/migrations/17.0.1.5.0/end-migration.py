import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if version == "17.0.1.3.0":
        _logger.info(f"End-Migration started for version {version}")

        # Step 1: Drop temp_unique_id column if it exists
        cr.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'res_partner'
            AND column_name = 'temp_unique_id'
        """
        )

        if cr.fetchone()[0] > 0:
            cr.execute("ALTER TABLE res_partner DROP COLUMN temp_unique_id")

        # Step 2: Remove cron job
        cr.execute("SELECT COUNT(*) FROM ir_cron WHERE cron_name = 'Reference ID Generation Cron Job'")
        if cr.fetchone()[0] > 0:
            cr.execute("DELETE FROM ir_cron WHERE cron_name = 'Reference ID Generation Cron Job'")

        # Step 3: Remove fields from res.config.settings if they exist
        cr.execute("SELECT COUNT(*) FROM ir_model_fields WHERE model = 'res.config.settings'")
        if cr.fetchone()[0] > 0:
            cr.execute(
                """
                DELETE FROM ir_model_fields
                WHERE model = 'res.config.settings'
                AND name IN (
                    'id_generator_base_api_url', 'id_generator_auth_url',
                    'id_generator_auth_client_id', 'id_generator_auth_client_secret',
                    'id_generator_auth_grant_type', 'id_generator_api_timeout'
                )
            """
            )
        # Step 4: Remove XML-defined records if they exist
        cr.execute(
            """
            SELECT COUNT(*) FROM ir_model_data
            WHERE model IN ('g2p.pending.reference_id', 'g2p.reference_id.config')
        """
        )
        if cr.fetchone()[0] > 0:
            cr.execute(
                """
                DELETE FROM ir_model_data
                WHERE model IN ('g2p.pending.reference_id', 'g2p.reference_id.config')
            """
            )

        # Step 5: Remove models from ir_model if they exist
        cr.execute(
            """
            SELECT COUNT(*) FROM ir_model
            WHERE model IN ('g2p.pending.reference_id', 'g2p.reference_id.config')
        """
        )
        if cr.fetchone()[0] > 0:
            cr.execute(
                """
                DELETE FROM ir_model
                WHERE model IN ('g2p.pending.reference_id', 'g2p.reference_id.config')
            """
            )

        # Step 6: Drop tables if they exist
        cr.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'g2p_pending_reference_id'"
        )
        if cr.fetchone()[0] > 0:
            cr.execute("DROP TABLE g2p_pending_reference_id CASCADE")

        cr.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'g2p_reference_id_config'"
        )
        if cr.fetchone()[0] > 0:
            cr.execute("DROP TABLE g2p_reference_id_config CASCADE")

        _logger.info(f"End-Migration completed successfully for version {version}")
