import json

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestWorkflow(TransactionCase):
    """Test cases for the change request workflow."""

    def setUp(self):
        super().setUp()
        # Create test users
        self.user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "email": "test@example.com",
            }
        )

        self.approver = self.env["res.users"].create(
            {
                "name": "Test Approver",
                "login": "test_approver",
                "email": "approver@example.com",
            }
        )

        # Create test group kind
        self.group_kind = self.env["g2p.group.kind"].create(
            {
                "name": "Test Group Kind",
            }
        )

        # Create test registrant
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Registrant",
                "is_registrant": True,
                "is_group": False,
                "unique_id": "TEST001",
                "company_id": self.env.company.id,
            }
        )

    def test_submit_workflow(self):
        """Test submit workflow."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
                "description": "Test submit workflow",
            }
        )

        # Initially in draft state
        self.assertEqual(change_request.state, "draft")
        self.assertTrue(change_request.can_submit)

        # Submit the change request
        change_request.action_submit()

        # Should be in submitted state
        self.assertEqual(change_request.state, "submitted")
        self.assertFalse(change_request.can_submit)
        self.assertTrue(change_request.can_approve)
        self.assertTrue(change_request.can_reject)

        # Should have created approval activity
        activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "g2p.change.request"),
                ("res_id", "=", change_request.id),
            ]
        )
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].activity_type_id.name, "To Do")

    def test_approve_workflow(self):
        """Test approve workflow."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
                "description": "Test approve workflow",
            }
        )

        # Submit first
        change_request.action_submit()

        # Approve the change request
        change_request.action_approve()

        # Should be in approved state
        self.assertEqual(change_request.state, "approved")
        self.assertFalse(change_request.can_submit)
        self.assertFalse(change_request.can_approve)
        self.assertFalse(change_request.can_reject)

        # Should have approver set
        self.assertEqual(change_request.approver_id, self.env.user)

    def test_reject_workflow(self):
        """Test reject workflow."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
                "description": "Test reject workflow",
            }
        )

        # Submit first
        change_request.action_submit()

        # Reject the change request
        change_request.action_reject()

        # Should be in rejected state
        self.assertEqual(change_request.state, "rejected")
        self.assertFalse(change_request.can_submit)
        self.assertFalse(change_request.can_approve)
        self.assertFalse(change_request.can_reject)

        # Should have approver set
        self.assertEqual(change_request.approver_id, self.env.user)

    def test_workflow_permissions(self):
        """Test workflow permissions."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
                "description": "Test workflow permissions",
            }
        )

        # Cannot approve/reject from draft state
        with self.assertRaises(ValidationError):
            change_request.action_approve()

        with self.assertRaises(ValidationError):
            change_request.action_reject()

        # Submit first
        change_request.action_submit()

        # Cannot submit from submitted state
        with self.assertRaises(ValidationError):
            change_request.action_submit()

        # Approve
        change_request.action_approve()

        # Cannot submit/approve/reject from approved state
        with self.assertRaises(ValidationError):
            change_request.action_submit()

        with self.assertRaises(ValidationError):
            change_request.action_approve()

        with self.assertRaises(ValidationError):
            change_request.action_reject()

    def test_create_workflow_with_implementation(self):
        """Test create workflow with actual implementation."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
                "description": "Test create workflow with implementation",
            }
        )

        # Update draft record with actual data
        change_request.draft_record_id.write(
            {
                "name": "John Doe",
                "given_name": "John",
                "family_name": "Doe",
                "phone": "1234567890",
            }
        )

        # Submit and approve
        change_request.action_submit()
        change_request.action_approve()

        # Should have created a registrant
        self.assertIsNotNone(change_request.partner_id)
        self.assertEqual(change_request.partner_id.name, "John Doe")
        self.assertEqual(change_request.partner_id.phone, "1234567890")

    def test_modify_workflow(self):
        """Test modify workflow."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.partner.id,
                "description": "Test modify workflow",
            }
        )

        # Update draft record
        change_request.draft_record_id.write(
            {
                "name": "Modified Registrant",
                "phone": "9876543210",
            }
        )

        # Submit and approve
        change_request.action_submit()
        change_request.action_approve()

        # Registrant should be updated
        self.assertEqual(self.partner.name, "Modified Registrant")
        self.assertEqual(self.partner.phone, "9876543210")

    def test_delete_workflow(self):
        """Test delete workflow."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "delete",
                "partner_id": self.partner.id,
                "description": "Test delete workflow",
            }
        )

        # Submit and approve
        change_request.action_submit()
        change_request.action_approve()

        # Registrant should be deactivated
        self.assertFalse(self.partner.active)

    def test_group_member_workflow(self):
        """Test group member workflow."""
        # Create a group
        group = self.env["res.partner"].create(
            {
                "name": "Test Group",
                "is_registrant": True,
                "is_group": True,
                "unique_id": "GRP001",
                "company_id": self.env.company.id,
            }
        )

        # Create individual members
        _member1 = self.env["res.partner"].create(
            {
                "name": "Member 1",
                "is_registrant": True,
                "is_group": False,
                "unique_id": "MEM001",
                "company_id": self.env.company.id,
            }
        )

        _member2 = self.env["res.partner"].create(
            {
                "name": "Member 2",
                "is_registrant": True,
                "is_group": False,
                "unique_id": "MEM002",
                "company_id": self.env.company.id,
            }
        )

        # Create change request for group
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": group.id,
                "description": "Test group member workflow",
            }
        )

        # Add draft members
        draft_member1 = self.env["g2p.draft.record"].create(
            {
                "name": "Draft Member 1",
                "is_group": False,
            }
        )

        draft_member2 = self.env["g2p.draft.record"].create(
            {
                "name": "Draft Member 2",
                "is_group": False,
            }
        )

        change_request.draft_record_id.write(
            {
                "group_member_ids_json": json.dumps(
                    [
                        {"draft_id": draft_member1.id, "name": "Draft Member 1"},
                        {"draft_id": draft_member2.id, "name": "Draft Member 2"},
                    ]
                )
            }
        )

        # Submit and approve
        change_request.action_submit()
        change_request.action_approve()

        # Group should have members
        self.assertEqual(len(group.draft_member_ids), 2)

    def test_validation_before_submit(self):
        """Test validation before submit."""
        # Create change request without description
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
            }
        )

        # Should be able to submit (description is optional)
        change_request.action_submit()
        self.assertEqual(change_request.state, "submitted")

        # Create change request with short description
        change_request2 = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
                "description": "Short",
            }
        )

        # Should not be able to submit
        with self.assertRaises(ValidationError):
            change_request2.action_submit()

    def test_workflow_messages(self):
        """Test workflow messages."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
                "description": "Test workflow messages",
            }
        )

        # Submit
        change_request.action_submit()
        messages = change_request.message_ids
        self.assertTrue(any("submitted" in msg.body for msg in messages))

        # Approve
        change_request.action_approve()
        messages = change_request.message_ids
        self.assertTrue(any("approved" in msg.body for msg in messages))

    def test_workflow_activities(self):
        """Test workflow activities."""
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "create",
                "is_group": False,
                "description": "Test workflow activities",
            }
        )

        # Submit
        change_request.action_submit()
        activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "g2p.change.request"),
                ("res_id", "=", change_request.id),
            ]
        )
        self.assertEqual(len(activities), 1)

        # Approve
        change_request.action_approve()
        activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "g2p.change.request"),
                ("res_id", "=", change_request.id),
            ]
        )
        self.assertEqual(len(activities), 0)  # Activities should be closed
