import json

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):
    """Test cases for the res.partner model extensions."""

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

        # Create test group kind
        self.group_kind = self.env["g2p.group.kind"].create(
            {
                "name": "Test Group Kind",
            }
        )

        # Create test partners
        self.individual = self.env["res.partner"].create(
            {
                "name": "Test Individual",
                "is_registrant": True,
                "is_group": False,
                "unique_id": "IND001",
                "company_id": self.env.company.id,
            }
        )

        self.group = self.env["res.partner"].create(
            {
                "name": "Test Group",
                "is_registrant": True,
                "is_group": True,
                "unique_id": "GRP001",
                "company_id": self.env.company.id,
            }
        )

    def test_computed_fields(self):
        """Test computed fields on res.partner."""
        # Initially no active drafts
        self.assertFalse(self.individual.has_active_draft)
        self.assertFalse(self.individual.active_change_request_id)

        # Create a change request
        change_request = self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.individual.id,
                "description": "Test computed fields",
            }
        )

        # Should have active draft
        self.assertTrue(self.individual.has_active_draft)
        self.assertEqual(self.individual.active_change_request_id, change_request)

    def test_create_change_request_action(self):
        """Test creating change request from partner action."""
        # Test individual
        action = self.individual.action_create_change_request()
        self.assertEqual(action["res_model"], "g2p.change.request")
        self.assertEqual(action["view_mode"], "form")

        # Test group
        action = self.group.action_create_change_request()
        self.assertEqual(action["res_model"], "g2p.change.request")
        self.assertEqual(action["view_mode"], "form")

    def test_create_change_request_with_active_draft(self):
        """Test creating change request when partner already has active draft."""
        # Create first change request
        first_cr = self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.individual.id,
                "description": "First request",
            }
        )

        # Try to create second change request
        action = self.individual.action_create_change_request()

        # Should return action to existing change request
        self.assertEqual(action["res_model"], "g2p.change.request")
        self.assertEqual(action["res_id"], first_cr.id)

    def test_write_restriction_with_active_draft(self):
        """Test that partner cannot be modified directly when it has active draft."""
        # Create change request
        self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.individual.id,
                "description": "Test write restriction",
            }
        )

        # Should not allow direct modification
        with self.assertRaises(ValidationError):
            self.individual.write({"name": "Modified Name"})

        # Should allow with force_write context
        self.individual.with_context(force_write=True).write({"name": "Modified Name"})

    def test_draft_member_ids_computation(self):
        """Test draft_member_ids computation for groups."""
        # Create a group change request
        _change_request = self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.group.id,
                "description": "Test draft members",
            }
        )

        # Initially no draft members
        self.assertEqual(len(self.group.draft_member_ids), 0)

        # Add draft members to the draft record
        draft_member = self.env["g2p.draft.record"].create(
            {
                "name": "Draft Member",
                "is_group": False,
            }
        )

        _change_request.draft_record_id.write(
            {"group_member_ids_json": json.dumps([{"draft_id": draft_member.id, "name": "Draft Member"}])}
        )

        # Should have draft members
        self.assertEqual(len(self.group.draft_member_ids), 1)
        self.assertEqual(self.group.draft_member_ids[0], draft_member)

    def test_add_draft_members_action(self):
        """Test add draft members action for groups."""
        # Create a group change request
        _change_request = self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.group.id,
                "description": "Test add draft members",
            }
        )

        # Test action for group
        action = self.group.action_add_draft_members()
        self.assertEqual(action["res_model"], "g2p.draft.group.add.members.wizard")
        self.assertEqual(action["view_mode"], "form")

        # Test action for individual (should fail)
        with self.assertRaises(UserError):
            self.individual.action_add_draft_members()

    def test_add_draft_members_no_active_request(self):
        """Test add draft members when no active change request."""
        with self.assertRaises(UserError):
            self.group.action_add_draft_members()

    def test_create_draft_from_partner(self):
        """Test creating draft record from partner."""
        draft_record = self.individual._create_draft_from_partner()

        self.assertEqual(draft_record.name, self.individual.name)
        self.assertEqual(draft_record.is_group, self.individual.is_group)
        self.assertEqual(draft_record.phone, self.individual.phone)

    def test_validation_for_change_request(self):
        """Test validation for change request creation."""
        # Test valid partner
        self.assertTrue(self.individual._validate_for_change_request())

        # Test inactive partner
        self.individual.write({"active": False})
        with self.assertRaises(ValidationError):
            self.individual._validate_for_change_request()

        # Test partner with active draft
        self.individual.write({"active": True})
        self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.individual.id,
                "description": "Test validation",
            }
        )

        with self.assertRaises(ValidationError):
            self.individual._validate_for_change_request()

    def test_change_request_consistency_constraint(self):
        """Test change request consistency constraint."""
        # Create first change request
        self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.individual.id,
                "description": "First request",
            }
        )

        # Create second change request of different type (should be allowed)
        self.env["g2p.change.request"].create(
            {
                "type": "delete",
                "partner_id": self.individual.id,
                "description": "Second request",
            }
        )

        # Both should exist
        self.assertEqual(len(self.individual.change_request_ids), 2)

    def test_active_with_change_requests_constraint(self):
        """Test constraint preventing deactivation with active change requests."""
        # Create change request
        self.env["g2p.change.request"].create(
            {
                "type": "modify",
                "partner_id": self.individual.id,
                "description": "Test deactivation constraint",
            }
        )

        # Should not allow deactivation
        with self.assertRaises(ValidationError):
            self.individual.write({"active": False})

        # Should allow deactivation after change request is completed
        change_request = self.individual.change_request_ids[0]
        change_request.action_submit()
        change_request.action_approve()

        # Now should allow deactivation
        self.individual.write({"active": False})
