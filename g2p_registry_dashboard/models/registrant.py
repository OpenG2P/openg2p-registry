# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartnerDashboard(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_dashboard_data(self):
        """Fetch data from materialized view and prepare it for charts."""
        company_id = self.env.company.id

        # First check if the materialized view exists
        self.env.cr.execute(
            """
            SELECT matviewname
            FROM pg_matviews
            WHERE matviewname = 'g2p_registry_dashboard_data';
        """
        )

        if not self.env.cr.fetchone():
            # Materialized view doesn't exist, try to create it
            try:
                from . import init_materialized_view

                init_materialized_view(self.env)
            except Exception as e:
                _logger.warning("Could not create materialized view: %s", str(e))

        query = """
            SELECT total_registrants, gender_spec, age_distribution
            FROM g2p_registry_dashboard_data
            WHERE company_id = %s
        """
        self.env.cr.execute(query, (company_id,))
        result = self.env.cr.fetchone()

        # Handle case where no data is found
        if result is None:
            return {
                "total_individuals": 0,
                "total_groups": 0,
                "gender_distribution": {},
                "age_distribution": {
                    "Below 18": 0,
                    "18 to 30": 0,
                    "31 to 40": 0,
                    "41 to 50": 0,
                    "Above 50": 0,
                },
            }

        total_registrants, gender_spec, age_distribution = result

        # Handle case where data might be None or malformed
        if total_registrants is None:
            total_registrants = {}
        if gender_spec is None:
            gender_spec = {}
        if age_distribution is None:
            age_distribution = {}

        return {
            "total_individuals": total_registrants.get("total_individuals", 0),
            "total_groups": total_registrants.get("total_groups", 0),
            "gender_distribution": gender_spec,
            "age_distribution": {
                "Below 18": age_distribution.get("below_18", 0),
                "18 to 30": age_distribution.get("18_to_30", 0),
                "31 to 40": age_distribution.get("31_to_40", 0),
                "41 to 50": age_distribution.get("41_to_50", 0),
                "Above 50": age_distribution.get("above_50", 0),
            },
        }

    @api.model
    def refresh_dashboard_data(self):
        """Manually refresh the dashboard materialized views."""
        try:
            from .. import init_materialized_view

            init_materialized_view(self.env)
            return {"success": True, "message": "Dashboard data refreshed successfully"}
        except Exception as e:
            _logger.error("Error refreshing dashboard data: %s", str(e))
            return {"success": False, "message": f"Error refreshing dashboard data: {str(e)}"}
