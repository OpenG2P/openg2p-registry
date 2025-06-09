import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if version in ["17.0.1.3.0", "17.0.1.4.0"]:
        _logger.info(f"Pre-migration started for {version}")

        # Check and delete from ir_config_parameter
        cr.execute("SELECT COUNT(*) FROM ir_config_parameter WHERE key = 'g2p_odk_importer.enable_odk';")
        if cr.fetchone()[0] > 0:
            cr.execute("DELETE FROM ir_config_parameter WHERE key = 'g2p_odk_importer.enable_odk';")

        # Check and delete 'g2p_odk_importer.enable_odk_async'
        if version == "17.0.1.4.0":
            cr.execute(
                "SELECT COUNT(*) FROM ir_config_parameter WHERE key ='g2p_odk_importer.enable_odk_async';"
            )
            if cr.fetchone()[0] > 0:
                cr.execute("DELETE FROM ir_config_parameter WHERE key ='g2p_odk_importer.enable_odk_async';")

        # Check and delete from ir_ui_view
        cr.execute(
            "SELECT COUNT(*) FROM ir_ui_view WHERE name = 'odk.res.config.settings.view.inherit.setup';"
        )
        if cr.fetchone()[0] > 0:
            # Delete all the child views which has inherited this view
            cr.execute(
                """
                DELETE FROM ir_ui_view
                WHERE inherit_id = (
                    SELECT id FROM ir_ui_view
                    WHERE name = 'odk.res.config.settings.view.inherit.setup'
                )
            """
            )

            cr.execute("DELETE FROM ir_ui_view WHERE name = 'odk.res.config.settings.view.inherit.setup';")

        _logger.info(f"Pre-migration completed successfully for {version}")
