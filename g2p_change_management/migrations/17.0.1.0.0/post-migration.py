# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Add performance optimization indexes."""
    
    # Add indexes for better query performance
    indexes = [
        # Change Request indexes
        "CREATE INDEX IF NOT EXISTS idx_change_request_state_type ON change_request (state, type);",
        "CREATE INDEX IF NOT EXISTS idx_change_request_requester_state ON change_request (requester_id, state);",
        "CREATE INDEX IF NOT EXISTS idx_change_request_partner_state ON change_request (partner_id, state);",
        "CREATE INDEX IF NOT EXISTS idx_change_request_create_date ON change_request (create_date);",
        "CREATE INDEX IF NOT EXISTS idx_change_request_name ON change_request (name);",
        
        # Res Partner indexes
        "CREATE INDEX IF NOT EXISTS idx_res_partner_has_active_draft ON res_partner (has_active_draft);",
        "CREATE INDEX IF NOT EXISTS idx_res_partner_active_cr ON res_partner (active_change_request_id);",
        
        # Draft Record indexes
        "CREATE INDEX IF NOT EXISTS idx_draft_record_state ON draft_record (state);",
        "CREATE INDEX IF NOT EXISTS idx_draft_record_is_group ON draft_record (is_group);",
        "CREATE INDEX IF NOT EXISTS idx_draft_record_state_group ON draft_record (state, is_group);",
    ]
    
    for index_sql in indexes:
        try:
            cr.execute(index_sql)
            _logger.info(f"Created performance index: {index_sql}")
        except Exception as e:
            _logger.warning(f"Failed to create index: {index_sql}, Error: {e}")
    
    # Analyze tables for query optimization
    tables = ['change_request', 'res_partner', 'draft_record']
    
    for table in tables:
        try:
            cr.execute(f"ANALYZE {table};")
            _logger.info(f"Analyzed table for optimization: {table}")
        except Exception as e:
            _logger.warning(f"Failed to analyze table {table}: {e}")
    
    _logger.info("Performance optimization migration completed successfully")
