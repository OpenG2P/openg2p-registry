import logging

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestBulkOperations(TransactionCase):
    """Test bulk operations functionality"""

    def setUp(self):
        super().setUp()

        # Create test users
        self.user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "testuser",
                "email": "test@example.com",
                "company_id": self.env.company.id,
            }
        )

        self.approver = self.env["res.users"].create(
            {
                "name": "Test Approver",
                "login": "testapprover",
                "email": "approver@example.com",
                "company_id": self.env.company.id,
            }
        )

        # Create test change requests
        self.change_request_1 = self.env["g2p.change.request"].create(
            {
                "name": "Test CR 1",
                "type": "create",
                "is_group": False,
                "requester_id": self.user.id,
                "state": "draft",
                "description": "Test change request 1",
            }
        )

        self.change_request_2 = self.env["g2p.change.request"].create(
            {
                "name": "Test CR 2",
                "type": "create",
                "is_group": False,
                "requester_id": self.user.id,
                "state": "draft",
                "description": "Test change request 2",
            }
        )

        self.change_request_3 = self.env["g2p.change.request"].create(
            {
                "name": "Test CR 3",
                "type": "create",
                "is_group": False,
                "requester_id": self.user.id,
                "state": "submitted",
                "description": "Test change request 3",
            }
        )

    def test_bulk_approve_wizard_creation(self):
        """Test bulk approval wizard creation"""
        wizard = (
            self.env["g2p.change.request.bulk.wizard"]
            .with_context(active_ids=[self.change_request_3.id], operation_type="approve")
            .create({})
        )

        self.assertEqual(wizard.operation_type, "approve")
        self.assertEqual(len(wizard.change_request_ids), 1)
        self.assertEqual(wizard.change_request_ids[0], self.change_request_3)

    def test_bulk_reject_wizard_creation(self):
        """Test bulk rejection wizard creation"""
        wizard = (
            self.env["g2p.change.request.bulk.wizard"]
            .with_context(active_ids=[self.change_request_3.id], operation_type="reject")
            .create({})
        )

        self.assertEqual(wizard.operation_type, "reject")
        self.assertEqual(len(wizard.change_request_ids), 1)

    def test_bulk_submit_wizard_creation(self):
        """Test bulk submission wizard creation"""
        wizard = (
            self.env["g2p.change.request.bulk.wizard"]
            .with_context(
                active_ids=[self.change_request_1.id, self.change_request_2.id], operation_type="submit"
            )
            .create({})
        )

        self.assertEqual(wizard.operation_type, "submit")
        self.assertEqual(len(wizard.change_request_ids), 2)

    def test_bulk_operation_summary(self):
        """Test operation summary computation"""
        wizard = (
            self.env["g2p.change.request.bulk.wizard"]
            .with_context(
                active_ids=[self.change_request_1.id, self.change_request_2.id], operation_type="submit"
            )
            .create({})
        )

        expected_summary = "This will Submit 2 change request(s)."
        self.assertEqual(wizard.operation_summary, expected_summary)

    def test_bulk_approve_action(self):
        """Test bulk approval action"""
        # Create wizard with submitted change request
        wizard = (
            self.env["g2p.change.request.bulk.wizard"]
            .with_context(active_ids=[self.change_request_3.id], operation_type="approve")
            .create({"reason": "Bulk approval test"})
        )

        # Mock the approval method to avoid actual implementation
        original_approve = self.change_request_3.action_approve
        self.change_request_3.action_approve = lambda: None

        try:
            result = wizard.action_confirm()
            self.assertIsNotNone(result)
        finally:
            # Restore original method
            self.change_request_3.action_approve = original_approve

    def test_bulk_operation_validation(self):
        """Test bulk operation validation"""
        wizard = self.env["g2p.change.request.bulk.wizard"].create(
            {
                "operation_type": "approve",
                "change_request_ids": [(6, 0, [])],  # Empty list
            }
        )

        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_bulk_assign_wizard(self):
        """Test bulk assignment wizard"""
        wizard = (
            self.env["g2p.change.request.bulk.wizard"]
            .with_context(
                active_ids=[self.change_request_1.id, self.change_request_2.id], operation_type="assign"
            )
            .create({"assign_to_user_id": self.approver.id, "reason": "Bulk assignment test"})
        )

        self.assertEqual(wizard.operation_type, "assign")
        self.assertEqual(wizard.assign_to_user_id, self.approver)
        self.assertEqual(len(wizard.change_request_ids), 2)

    def test_change_request_bulk_methods(self):
        """Test change request bulk action methods"""
        change_requests = self.change_request_1 + self.change_request_2

        # Test bulk approve method
        result = change_requests.action_bulk_approve()
        self.assertEqual(result["res_model"], "g2p.change.request.bulk.wizard")
        self.assertEqual(result["context"]["operation_type"], "approve")

        # Test bulk reject method
        result = change_requests.action_bulk_reject()
        self.assertEqual(result["res_model"], "g2p.change.request.bulk.wizard")
        self.assertEqual(result["context"]["operation_type"], "reject")

        # Test bulk submit method
        result = change_requests.action_bulk_submit()
        self.assertEqual(result["res_model"], "g2p.change.request.bulk.wizard")
        self.assertEqual(result["context"]["operation_type"], "submit")

    def test_empty_selection_validation(self):
        """Test validation when no records are selected"""
        empty_records = self.env["g2p.change.request"]

        with self.assertRaises(UserError):
            empty_records.action_bulk_approve()
