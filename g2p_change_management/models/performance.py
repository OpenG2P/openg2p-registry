# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ChangeRequestPerformance(models.Model):
    """Performance optimization mixin for Change Request model."""
    _name = "change.request.performance"
    _description = "Change Request Performance Optimizations"

    @api.model
    def _get_performance_config(self):
        """Get performance configuration settings."""
        return {
            'batch_size': 100,
            'cache_timeout': 300,  # 5 minutes
            'max_records_per_query': 1000,
        }

    @api.model
    def _optimize_search_domain(self, domain):
        """Optimize search domain for better performance."""
        # Move indexed fields to the beginning of the domain
        indexed_fields = ['state', 'type', 'requester_id', 'partner_id', 'create_date']
        optimized_domain = []
        remaining_domain = []
        
        for condition in domain:
            if isinstance(condition, (list, tuple)) and len(condition) == 3:
                field_name = condition[0]
                if field_name in indexed_fields:
                    optimized_domain.append(condition)
                else:
                    remaining_domain.append(condition)
            else:
                remaining_domain.append(condition)
        
        return optimized_domain + remaining_domain

    @api.model
    def _batch_process_records(self, records, batch_size=None):
        """Process records in batches for better performance."""
        if batch_size is None:
            batch_size = self._get_performance_config()['batch_size']
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            yield batch

    @api.model
    def _get_cached_data(self, cache_key, compute_func, *args, **kwargs):
        """Get cached data or compute if not cached."""
        if not hasattr(self.env, '_change_request_cache'):
            self.env._change_request_cache = {}
        
        cache = self.env._change_request_cache
        if cache_key not in cache:
            cache[cache_key] = compute_func(*args, **kwargs)
        
        return cache[cache_key]

    @api.model
    def _clear_cache(self, cache_key=None):
        """Clear cache for specific key or all cache."""
        if not hasattr(self.env, '_change_request_cache'):
            return
        
        cache = self.env._change_request_cache
        if cache_key:
            cache.pop(cache_key, None)
        else:
            cache.clear()


class ResPartnerPerformance(models.Model):
    """Performance optimization mixin for Res Partner model."""
    _name = "res.partner.performance"
    _description = "Res Partner Performance Optimizations"

    @api.model
    def _get_partners_with_active_drafts(self, limit=None):
        """Efficiently get partners with active drafts."""
        domain = [('has_active_draft', '=', True)]
        if limit:
            domain.append(('id', 'in', self.search([], limit=limit).ids))
        
        return self.search(domain)

    @api.model
    def _get_partners_by_change_request_type(self, cr_type, limit=None):
        """Get partners by change request type efficiently."""
        domain = [
            ('change_request_ids.type', '=', cr_type),
            ('change_request_ids.state', 'in', ['draft', 'submitted'])
        ]
        
        if limit:
            return self.search(domain, limit=limit)
        return self.search(domain)

    @api.model
    def _bulk_update_change_request_names(self, partner_ids):
        """Bulk update change request names for multiple partners."""
        if not partner_ids:
            return
        
        # Get all change requests for these partners
        change_requests = self.env['change.request'].search([
            ('partner_id', 'in', partner_ids)
        ])
        
        # Update names in batches
        for batch in self._batch_process_records(change_requests):
            for cr in batch:
                cr._update_change_request_name()

    def _batch_process_records(self, records, batch_size=100):
        """Process records in batches for better performance."""
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            yield batch


class DraftRecordPerformance(models.Model):
    """Performance optimization mixin for Draft Record model."""
    _name = "draft.record.performance"
    _description = "Draft Record Performance Optimizations"

    @api.model
    def _get_draft_records_by_state(self, states, limit=None):
        """Get draft records by state efficiently."""
        domain = [('state', 'in', states)]
        if limit:
            return self.search(domain, limit=limit)
        return self.search(domain)

    @api.model
    def _get_draft_records_for_member_selection(self, limit=None):
        """Get draft records suitable for member selection."""
        domain = [
            ('is_group', '=', False),
            ('state', 'in', ['draft', 'submitted'])
        ]
        
        if limit:
            return self.search(domain, limit=limit)
        return self.search(domain)

    @api.model
    def _bulk_update_draft_record_names(self, draft_ids, name_pattern):
        """Bulk update draft record names."""
        if not draft_ids:
            return
        
        draft_records = self.browse(draft_ids)
        for i, draft in enumerate(draft_records):
            new_name = f"{name_pattern} - {i + 1}"
            draft.write({'name': new_name})


class PerformanceMonitoring(models.Model):
    """Performance monitoring and metrics."""
    _name = "change.request.performance.monitor"
    _description = "Change Request Performance Monitor"

    name = fields.Char('Operation Name', required=True)
    execution_time = fields.Float('Execution Time (seconds)')
    record_count = fields.Integer('Record Count')
    memory_usage = fields.Float('Memory Usage (MB)')
    timestamp = fields.Datetime('Timestamp', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', 'User')
    operation_type = fields.Selection([
        ('search', 'Search'),
        ('create', 'Create'),
        ('write', 'Write'),
        ('compute', 'Compute'),
        ('workflow', 'Workflow'),
    ], 'Operation Type')

    @api.model
    def log_performance(self, operation_name, execution_time, record_count=0, 
                       memory_usage=0, operation_type='compute'):
        """Log performance metrics."""
        self.create({
            'name': operation_name,
            'execution_time': execution_time,
            'record_count': record_count,
            'memory_usage': memory_usage,
            'operation_type': operation_type,
            'user_id': self.env.user.id,
        })

    @api.model
    def get_performance_stats(self, days=7):
        """Get performance statistics for the last N days."""
        domain = [
            ('timestamp', '>=', fields.Datetime.now() - 
             fields.timedelta(days=days))
        ]
        
        records = self.search(domain)
        
        stats = {
            'total_operations': len(records),
            'avg_execution_time': sum(records.mapped('execution_time')) / len(records) if records else 0,
            'max_execution_time': max(records.mapped('execution_time')) if records else 0,
            'total_records_processed': sum(records.mapped('record_count')),
            'avg_memory_usage': sum(records.mapped('memory_usage')) / len(records) if records else 0,
        }
        
        return stats

    @api.model
    def cleanup_old_records(self, days=30):
        """Clean up old performance records."""
        cutoff_date = fields.Datetime.now() - fields.timedelta(days=days)
        old_records = self.search([('timestamp', '<', cutoff_date)])
        old_records.unlink()
        _logger.info(f"Cleaned up {len(old_records)} old performance records")


class DatabaseOptimization(models.Model):
    """Database optimization utilities."""
    _name = "change.request.db.optimization"
    _description = "Change Request Database Optimization"

    @api.model
    def create_indexes(self):
        """Create additional database indexes for performance."""
        # This would typically be done in a migration script
        # but we can provide the SQL here for reference
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_change_request_state_type ON change_request (state, type);",
            "CREATE INDEX IF NOT EXISTS idx_change_request_requester_state ON change_request (requester_id, state);",
            "CREATE INDEX IF NOT EXISTS idx_change_request_partner_state ON change_request (partner_id, state);",
            "CREATE INDEX IF NOT EXISTS idx_change_request_create_date ON change_request (create_date);",
            "CREATE INDEX IF NOT EXISTS idx_res_partner_has_active_draft ON res_partner (has_active_draft);",
            "CREATE INDEX IF NOT EXISTS idx_res_partner_active_cr ON res_partner (active_change_request_id);",
        ]
        
        for index_sql in indexes:
            try:
                self.env.cr.execute(index_sql)
                _logger.info(f"Created index: {index_sql}")
            except Exception as e:
                _logger.warning(f"Failed to create index: {index_sql}, Error: {e}")

    @api.model
    def analyze_tables(self):
        """Analyze database tables for optimization."""
        tables = ['change_request', 'res_partner', 'draft_record']
        
        for table in tables:
            try:
                self.env.cr.execute(f"ANALYZE {table};")
                _logger.info(f"Analyzed table: {table}")
            except Exception as e:
                _logger.warning(f"Failed to analyze table {table}: {e}")

    @api.model
    def vacuum_tables(self):
        """Vacuum database tables to reclaim space."""
        tables = ['change_request', 'res_partner', 'draft_record']
        
        for table in tables:
            try:
                self.env.cr.execute(f"VACUUM {table};")
                _logger.info(f"Vacuumed table: {table}")
            except Exception as e:
                _logger.warning(f"Failed to vacuum table {table}: {e}")

    @api.model
    def get_table_stats(self):
        """Get table statistics for monitoring."""
        stats = {}
        
        tables = ['change_request', 'res_partner', 'draft_record']
        
        for table in tables:
            try:
                # Get row count
                self.env.cr.execute(f"SELECT COUNT(*) FROM {table};")
                row_count = self.env.cr.fetchone()[0]
                
                # Get table size
                self.env.cr.execute(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table}')) as size;
                """)
                table_size = self.env.cr.fetchone()[0]
                
                stats[table] = {
                    'row_count': row_count,
                    'table_size': table_size,
                }
                
            except Exception as e:
                _logger.warning(f"Failed to get stats for table {table}: {e}")
                stats[table] = {'error': str(e)}
        
        return stats
