import logging

from odoo import _, models
from odoo.exceptions import MissingError

_logger = logging.getLogger(__name__)


class DashboardCron(models.Model):
    _inherit = "ir.cron"

    def _refresh_dashboard_materialized_view(self):
        """
        Refreshes all the materialized views related to the Dashboard.
        """
        cr = self.env.cr
        matviews_to_refresh = [
            "g2p_gender_count_view",
            "g2p_age_distribution_view",
            "g2p_total_registrants_view",
            "g2p_sr_dashboard_data",
        ]

        for matview in matviews_to_refresh:
            try:
                cr.execute(
                    """
                    SELECT matviewname
                    FROM pg_matviews
                    WHERE matviewname = %s;
                """,
                    (matview,),
                )

                if not cr.fetchall():
                    raise MissingError(
                        _("Materialized view '%s' does not exist. Please create it first.") % matview
                    )

                cr.execute(f"REFRESH MATERIALIZED VIEW {matview}")  # pylint: disable=sql-injection

            except Exception as exc:
                _logger.error("Error refreshing materialized view '%s': %s", matview, str(exc))
                raise MissingError(
                    _("Failed to refresh materialized view '%s'. Please check the logs for details.")
                    % matview
                ) from exc
