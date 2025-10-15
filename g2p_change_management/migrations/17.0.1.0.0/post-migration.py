# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from psycopg2 import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Add performance optimization indexes."""

    # Add indexes for better query performance
    index_specs = [
        # (index_name, table, columns)
        ("idx_change_request_state_type", "change_request", ("state", "type")),
        (
            "idx_change_request_requester_state",
            "change_request",
            ("requester_id", "state"),
        ),
        (
            "idx_change_request_partner_state",
            "change_request",
            ("partner_id", "state"),
        ),
        ("idx_change_request_create_date", "change_request", ("create_date",)),
        ("idx_change_request_name", "change_request", ("name",)),
        ("idx_res_partner_has_active_draft", "res_partner", ("has_active_draft",)),
        ("idx_res_partner_active_cr", "res_partner", ("active_change_request_id",)),
        ("idx_draft_record_state", "draft_record", ("state",)),
        ("idx_draft_record_is_group", "draft_record", ("is_group",)),
        ("idx_draft_record_state_group", "draft_record", ("state", "is_group")),
    ]

    for index_name, table_name, columns in index_specs:
        try:
            create_idx = sql.SQL("CREATE INDEX IF NOT EXISTS {idx} ON {table} ({cols});").format(
                idx=sql.Identifier(index_name),
                table=sql.Identifier(table_name),
                cols=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
            )
            cr.execute(create_idx)
            _logger.info("Created performance index: %s", index_name)
        except Exception as exc:
            _logger.warning(
                "Failed to create index: %s on table %s. Error: %s",
                index_name,
                table_name,
                exc,
            )

    # Analyze tables for query optimization
    tables = ["change_request", "res_partner", "draft_record"]

    for table in tables:
        try:
            analyze_stmt = sql.SQL("ANALYZE {table};").format(table=sql.Identifier(table))
            cr.execute(analyze_stmt)
            _logger.info("Analyzed table for optimization: %s", table)
        except Exception as exc:
            _logger.warning("Failed to analyze table %s: %s", table, exc)

    _logger.info("Performance optimization migration completed successfully")
