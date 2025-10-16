import os
import time

import psutil

from odoo.tests.common import TransactionCase


class TestPerformance(TransactionCase):
    """Test cases for performance optimization."""

    def setUp(self):
        super().setUp()
        # Create test data for performance testing
        self.users = []
        self.partners = []
        self.change_requests = []

        # Create test users
        for i in range(10):
            user = self.env["res.users"].create(
                {
                    "name": f"Test User {i}",
                    "login": f"test_user_{i}",
                    "email": f"test{i}@example.com",
                    "company_id": self.env.company.id,
                }
            )
            self.users.append(user)

        # Create test partners
        for i in range(100):
            partner = self.env["res.partner"].create(
                {
                    "name": f"Test Partner {i}",
                    "is_registrant": True,
                    "is_group": i % 10 == 0,  # Every 10th partner is a group
                    "unique_id": f"TEST{i:03d}",
                    "company_id": self.env.company.id,
                }
            )
            self.partners.append(partner)

        # Create test group kind
        self.group_kind = self.env["g2p.group.kind"].create(
            {
                "name": "Test Group Kind",
            }
        )

    def _measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB

        result = func(*args, **kwargs)

        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB

        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory

        return result, execution_time, memory_usage

    def test_change_request_creation_performance(self):
        """Test performance of change request creation."""

        def create_change_requests():
            change_requests = []
            for i in range(50):
                cr = self.env["g2p.change.request"].create(
                    {
                        "type": "create",
                        "is_group": i % 5 == 0,
                        "group_kind_id": self.group_kind.id if i % 5 == 0 else False,
                        "description": f"Test change request {i}",
                    }
                )
                change_requests.append(cr)
            return change_requests

        result, execution_time, memory_usage = self._measure_execution_time(create_change_requests)

        # Performance assertions
        self.assertLess(execution_time, 10.0, "Change request creation should take less than 10 seconds")
        self.assertLess(memory_usage, 100.0, "Memory usage should be less than 100MB")
        self.assertEqual(len(result), 50, "Should create 50 change requests")

        # Log performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "change_request_creation_batch", execution_time, len(result), memory_usage, "create"
        )

    def test_change_request_search_performance(self):
        """Test performance of change request searches."""
        # Create test data
        for i in range(100):
            self.env["g2p.change.request"].create(
                {
                    "type": "create" if i % 2 == 0 else "modify",
                    "is_group": i % 10 == 0,
                    "description": f"Test change request {i}",
                }
            )

        def search_operations():
            # Test various search operations
            results = {}

            # Search by state
            results["draft"] = self.env["g2p.change.request"].search([("state", "=", "draft")])

            # Search by type
            results["create"] = self.env["g2p.change.request"].search([("type", "=", "create")])

            # Search by requester
            results["requester"] = self.env["g2p.change.request"].search(
                [("requester_id", "=", self.env.user.id)]
            )

            # Complex search
            results["complex"] = self.env["g2p.change.request"].search(
                [("state", "=", "draft"), ("type", "=", "create"), ("is_group", "=", False)]
            )

            return results

        result, execution_time, memory_usage = self._measure_execution_time(search_operations)

        # Performance assertions
        self.assertLess(execution_time, 5.0, "Search operations should take less than 5 seconds")
        self.assertLess(memory_usage, 50.0, "Memory usage should be less than 50MB")

        # Verify results
        self.assertGreater(len(result["draft"]), 0, "Should find draft change requests")
        self.assertGreater(len(result["create"]), 0, "Should find create change requests")

        # Log performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "change_request_search_operations",
            execution_time,
            sum(len(r) for r in result.values()),
            memory_usage,
            "search",
        )

    def test_computed_fields_performance(self):
        """Test performance of computed fields."""
        # Create change requests with partners
        change_requests = []
        for i in range(50):
            partner = self.partners[i % len(self.partners)]
            cr = self.env["g2p.change.request"].create(
                {
                    "type": "modify",
                    "partner_id": partner.id,
                    "description": f"Test modify request {i}",
                }
            )
            change_requests.append(cr)

        def compute_fields():
            # Trigger computation of all computed fields
            for cr in change_requests:
                # Access computed fields to trigger computation
                _ = cr.partner_name
                # draft_name field has been removed as redundant
                _ = cr.validation_summary
                _ = cr.can_submit
                _ = cr.can_approve
                _ = cr.can_reject
            return len(change_requests)

        result, execution_time, memory_usage = self._measure_execution_time(compute_fields)

        # Performance assertions
        self.assertLess(execution_time, 3.0, "Computed fields should compute quickly")
        self.assertLess(memory_usage, 30.0, "Memory usage should be reasonable")
        self.assertEqual(result, 50, "Should process all change requests")

        # Log performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "computed_fields_computation", execution_time, result, memory_usage, "compute"
        )

    def test_partner_computed_fields_performance(self):
        """Test performance of partner computed fields."""
        # Create change requests for partners
        for i in range(50):
            partner = self.partners[i % len(self.partners)]
            self.env["g2p.change.request"].create(
                {
                    "type": "modify",
                    "partner_id": partner.id,
                    "description": f"Test partner request {i}",
                }
            )

        def compute_partner_fields():
            # Access computed fields for all partners
            for partner in self.partners:
                _ = partner.has_active_draft
                _ = partner.active_change_request_id
                _ = partner.draft_member_ids
            return len(self.partners)

        result, execution_time, memory_usage = self._measure_execution_time(compute_partner_fields)

        # Performance assertions
        self.assertLess(execution_time, 5.0, "Partner computed fields should compute quickly")
        self.assertLess(memory_usage, 50.0, "Memory usage should be reasonable")
        self.assertEqual(result, 100, "Should process all partners")

        # Log performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "partner_computed_fields_computation", execution_time, result, memory_usage, "compute"
        )

    def test_workflow_performance(self):
        """Test performance of workflow operations."""
        # Create change requests
        change_requests = []
        for i in range(20):
            cr = self.env["g2p.change.request"].create(
                {
                    "type": "create",
                    "is_group": i % 5 == 0,
                    "description": f"Test workflow request {i}",
                }
            )
            change_requests.append(cr)

        def workflow_operations():
            # Submit all change requests
            for cr in change_requests:
                cr.action_submit()

            # Approve half of them
            for cr in change_requests[:10]:
                cr.action_approve()

            # Reject the other half
            for cr in change_requests[10:]:
                cr.action_reject()

            return len(change_requests)

        result, execution_time, memory_usage = self._measure_execution_time(workflow_operations)

        # Performance assertions
        self.assertLess(execution_time, 15.0, "Workflow operations should complete quickly")
        self.assertLess(memory_usage, 100.0, "Memory usage should be reasonable")
        self.assertEqual(result, 20, "Should process all change requests")

        # Verify workflow states
        approved_count = len(self.env["g2p.change.request"].search([("state", "=", "approved")]))
        rejected_count = len(self.env["g2p.change.request"].search([("state", "=", "rejected")]))

        self.assertEqual(approved_count, 10, "Should have 10 approved requests")
        self.assertEqual(rejected_count, 10, "Should have 10 rejected requests")

        # Log performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "workflow_operations_batch", execution_time, result, memory_usage, "workflow"
        )

    def test_bulk_operations_performance(self):
        """Test performance of bulk operations."""

        def bulk_create():
            # Create multiple change requests at once
            vals_list = []
            for i in range(100):
                vals_list.append(
                    {
                        "type": "create",
                        "is_group": i % 10 == 0,
                        "description": f"Bulk test request {i}",
                    }
                )

            return self.env["g2p.change.request"].create(vals_list)

        result, execution_time, memory_usage = self._measure_execution_time(bulk_create)

        # Performance assertions
        self.assertLess(execution_time, 8.0, "Bulk creation should be efficient")
        self.assertLess(memory_usage, 80.0, "Memory usage should be reasonable")
        self.assertEqual(len(result), 100, "Should create 100 change requests")

        # Log performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "bulk_change_request_creation", execution_time, len(result), memory_usage, "create"
        )

    def test_database_query_performance(self):
        """Test performance of database queries."""
        # Create test data
        for i in range(200):
            self.env["g2p.change.request"].create(
                {
                    "type": "create" if i % 3 == 0 else "modify",
                    "is_group": i % 20 == 0,
                    "description": f"Query test request {i}",
                }
            )

        def complex_queries():
            # Test complex queries
            results = {}

            # Query with multiple conditions
            results["complex"] = self.env["g2p.change.request"].search(
                [
                    ("state", "=", "draft"),
                    ("type", "in", ["create", "modify"]),
                    ("is_group", "=", False),
                    ("create_date", ">=", "2025-01-01"),
                ]
            )

            # Query with ordering
            results["ordered"] = self.env["g2p.change.request"].search(
                [("state", "=", "draft")], order="create_date desc", limit=50
            )

            # Query with grouping (using read)
            results["grouped"] = (
                self.env["g2p.change.request"].search([("state", "=", "draft")]).read(["type", "state"])
            )

            return results

        result, execution_time, memory_usage = self._measure_execution_time(complex_queries)

        # Performance assertions
        self.assertLess(execution_time, 3.0, "Complex queries should execute quickly")
        self.assertLess(memory_usage, 40.0, "Memory usage should be reasonable")

        # Verify results
        self.assertGreater(len(result["complex"]), 0, "Should find results for complex query")
        self.assertEqual(len(result["ordered"]), 50, "Should limit results correctly")
        self.assertGreater(len(result["grouped"]), 0, "Should read grouped data")

        # Log performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "complex_database_queries",
            execution_time,
            sum(len(r) if isinstance(r, list) else 1 for r in result.values()),
            memory_usage,
            "search",
        )

    def test_memory_usage_under_load(self):
        """Test memory usage under load."""

        def create_load():
            # Create a large number of records to test memory usage
            change_requests = []
            for i in range(500):
                cr = self.env["g2p.change.request"].create(
                    {
                        "type": "create",
                        "is_group": i % 50 == 0,
                        "description": f"Load test request {i}",
                    }
                )
                change_requests.append(cr)

            # Access computed fields for all records
            for cr in change_requests:
                _ = cr.partner_name
                _ = cr.validation_summary
                _ = cr.can_submit

            return len(change_requests)

        result, execution_time, memory_usage = self._measure_execution_time(create_load)

        # Performance assertions
        self.assertLess(execution_time, 30.0, "Load test should complete in reasonable time")
        self.assertLess(memory_usage, 200.0, "Memory usage should be reasonable under load")
        self.assertEqual(result, 500, "Should create all test records")

        # Log performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "memory_usage_load_test", execution_time, result, memory_usage, "create"
        )

    def test_performance_monitoring(self):
        """Test performance monitoring functionality."""
        # Log some performance metrics
        self.env["g2p.change.request.performance.monitor"].log_performance(
            "test_operation", 1.5, 100, 50.0, "compute"
        )

        # Get performance stats
        stats = self.env["g2p.change.request.performance.monitor"].get_performance_stats()

        # Verify stats
        self.assertGreater(stats["total_operations"], 0, "Should have logged operations")
        self.assertGreater(stats["avg_execution_time"], 0, "Should have average execution time")
        self.assertGreater(stats["total_records_processed"], 0, "Should have processed records")

        # Test cleanup
        self.env["g2p.change.request.performance.monitor"].cleanup_old_records(days=0)

        # Verify cleanup worked
        remaining_records = self.env["g2p.change.request.performance.monitor"].search([])
        self.assertEqual(len(remaining_records), 0, "Should have cleaned up all records")

    def test_database_optimization(self):
        """Test database optimization utilities."""
        # Test table stats
        stats = self.env["g2p.change.request.db.optimization"].get_table_stats()

        # Verify stats structure
        self.assertIn("change_request", stats, "Should have change_request stats")
        self.assertIn("res_partner", stats, "Should have res_partner stats")
        self.assertIn("draft_record", stats, "Should have draft_record stats")

        # Test analyze tables (should not raise exception)
        try:
            self.env["g2p.change.request.db.optimization"].analyze_tables()
        except Exception as e:
            self.fail(f"analyze_tables should not raise exception: {e}")

        # Test vacuum tables (should not raise exception)
        try:
            self.env["g2p.change.request.db.optimization"].vacuum_tables()
        except Exception as e:
            self.fail(f"vacuum_tables should not raise exception: {e}")

    def tearDown(self):
        """Clean up test data."""
        # Clean up performance monitoring records
        self.env["g2p.change.request.performance.monitor"].search([]).unlink()

        super().tearDown()
