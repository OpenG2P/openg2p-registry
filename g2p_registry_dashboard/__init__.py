# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from . import models

from odoo import _
from odoo.exceptions import MissingError
import logging

_logger = logging.getLogger(__name__)


def init_materialized_view(env):
    """
    Initializes or refreshes the materialized views for the res_partner_dashboard_data.
    """
    cr = env.cr

    matviews_to_check = [
        "g2p_gender_count_view",
        "g2p_age_distribution_view",
        "g2p_total_registrants_view",
        "g2p_sr_dashboard_data",
    ]

    try:
        cr.execute(
            """
            SELECT matviewname
            FROM pg_matviews
            WHERE matviewname IN %s;
        """,
            (tuple(matviews_to_check),),
        )

        existing_views = set([row[0] for row in cr.fetchall()])

        if "g2p_gender_count_view" not in existing_views:
            gender_query = """
                CREATE MATERIALIZED VIEW g2p_gender_count_view AS
                SELECT
                    rp.company_id,
                    gt.code AS gender,
                    COUNT(rp.id) AS gender_count
                FROM
                    res_partner rp
                LEFT JOIN
                    gender_type gt ON rp.gender = gt.value
                WHERE
                    rp.is_registrant = True
                    AND rp.active = True
                    AND rp.is_group = False
                GROUP BY
                    rp.company_id, gt.code;
            """
            cr.execute(gender_query)
            _logger.info("Created materialized view: g2p_gender_count_view")

        if "g2p_age_distribution_view" not in existing_views:
            age_distribution_query = """
                CREATE MATERIALIZED VIEW g2p_age_distribution_view AS
                SELECT
                    rp.company_id,
                    jsonb_build_object(
                        'below_18', COUNT(rp.id) FILTER (
                            WHERE EXTRACT(YEAR FROM AGE(rp.birthdate)) < 18
                        ),
                        '18_to_30', COUNT(rp.id) FILTER (
                            WHERE EXTRACT(YEAR FROM AGE(rp.birthdate)) BETWEEN 18 AND 30
                        ),
                        '31_to_40', COUNT(rp.id) FILTER (
                            WHERE EXTRACT(YEAR FROM AGE(rp.birthdate)) BETWEEN 31 AND 40
                        ),
                        '41_to_50', COUNT(rp.id) FILTER (
                            WHERE EXTRACT(YEAR FROM AGE(rp.birthdate)) BETWEEN 41 AND 50
                        ),
                        'above_50', COUNT(rp.id) FILTER (
                            WHERE EXTRACT(YEAR FROM AGE(rp.birthdate)) > 50
                        )
                    ) AS age_distribution
                FROM
                    res_partner rp
                WHERE
                    rp.is_registrant = True
                    AND rp.active = True
                    AND rp.is_group = False
                GROUP BY
                    rp.company_id;
            """
            cr.execute(age_distribution_query)
            _logger.info("Created materialized view: g2p_age_distribution_view")

        if "g2p_total_registrants_view" not in existing_views:
            total_registrants_query = """
                CREATE MATERIALIZED VIEW g2p_total_registrants_view AS
                SELECT
                    rp.company_id,
                    jsonb_build_object(
                        'total_individuals', COUNT(rp.id) FILTER (WHERE rp.is_group = False),
                        'total_groups', COUNT(rp.id) FILTER (WHERE rp.is_group = True)
                    ) AS total_registrants
                FROM
                    res_partner rp
                WHERE
                    rp.is_registrant = True
                    AND rp.active = True
                GROUP BY
                    rp.company_id;
            """
            cr.execute(total_registrants_query)
            _logger.info("Created materialized view: g2p_total_registrants_view")

        if "g2p_sr_dashboard_data" not in existing_views:
            dashboard_query = """
                CREATE MATERIALIZED VIEW g2p_sr_dashboard_data AS
                SELECT
                    trv.company_id,
                    trv.total_registrants,
                    COALESCE(
                        jsonb_object_agg(gc.gender, gc.gender_count) FILTER (WHERE gc.gender IS NOT NULL),
                        '{}'
                    ) AS gender_spec,
                    adv.age_distribution
                FROM
                    g2p_total_registrants_view trv
                LEFT JOIN
                    g2p_gender_count_view gc ON trv.company_id = gc.company_id
                LEFT JOIN
                    g2p_age_distribution_view adv ON trv.company_id = adv.company_id
                GROUP BY
                    trv.company_id, trv.total_registrants, adv.age_distribution;
            """
            cr.execute(dashboard_query)
            _logger.info("Created materialized view: g2p_sr_dashboard_data")

    except Exception as exc:
        _logger.error("Error while creating materialized views: %s", str(exc))
        raise MissingError(
            _(
                "Failed to create the materialized views."
                "Please check the logs for details or Manually create it."
            )
        ) from exc


def drop_materialized_view(env):
    """
    Drop all the materialized views related to the dashboard.
    """
    cr = env.cr

    matviews_to_drop = [
        "g2p_sr_dashboard_data",
        "g2p_gender_count_view",
        "g2p_age_distribution_view",
        "g2p_total_registrants_view",
    ]

    try:
        for matview in matviews_to_drop:
            cr.execute(f"DROP MATERIALIZED VIEW IF EXISTS {matview} CASCADE;")  # pylint: disable=sql-injection
            _logger.info("Dropped materialized view: %s", matview)

    except Exception as exc:
        _logger.error("Error while dropping materialized views: %s", str(exc))
        raise MissingError(
            _(
                "Failed to drop the materialized views."
                "Please check the logs for details or manually delete the view."
            )
        ) from exc
