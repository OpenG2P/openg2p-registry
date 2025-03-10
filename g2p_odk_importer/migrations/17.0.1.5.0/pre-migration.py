import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if version == "17.0.1.3.0":
        _logger.info(f"Pre-migration started for {version}")

        # Check and delete from ir_config_parameter
        cr.execute("SELECT COUNT(*) FROM ir_config_parameter WHERE key = 'g2p_odk_importer.enable_odk';")
        if cr.fetchone()[0] > 0:
            cr.execute("DELETE FROM ir_config_parameter WHERE key = 'g2p_odk_importer.enable_odk';")

        # Check and delete from ir_model_fields
        cr.execute(
            """
            SELECT COUNT(*) FROM ir_model_fields
            WHERE name = 'enable_odk' AND model = 'res.config.settings';
            """
        )
        if cr.fetchone()[0] > 0:
            cr.execute(
                "DELETE FROM ir_model_fields WHERE name = 'enable_odk' AND model = 'res.config.settings';"
            )

        # Check and delete from ir_ui_view
        cr.execute(
            "SELECT COUNT(*) FROM ir_ui_view WHERE name = 'odk.res.config.settings.view.inherit.setup';"
        )
        if cr.fetchone()[0] > 0:
            cr.execute("DELETE FROM ir_ui_view WHERE name = 'odk.res.config.settings.view.inherit.setup';")

        _logger.info(f"Pre-migration completed successfully for {version}")
