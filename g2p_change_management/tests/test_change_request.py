import json
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestChangeRequest(TransactionCase):
    """Test cases for the Change Request model."""

    def setUp(self):
        super().setUp()
        # Create test users
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'test@example.com',
        })
        
        self.approver = self.env['res.users'].create({
            'name': 'Test Approver',
            'login': 'test_approver',
            'email': 'approver@example.com',
        })
        
        # Create test group kind
        self.group_kind = self.env['g2p.group.kind'].create({
            'name': 'Test Group Kind',
        })
        
        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'is_registrant': True,
            'is_group': False,
            'unique_id': 'TEST001',
            'company_id': self.env.company.id,
        })

    def test_create_change_request(self):
        """Test creating a new change request."""
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': False,
            'description': 'Test create request',
        })
        
        self.assertEqual(change_request.type, 'create')
        self.assertEqual(change_request.state, 'draft')
        self.assertEqual(change_request.requester_id, self.env.user)
        self.assertIsNotNone(change_request.draft_record_id)
        self.assertTrue(change_request.name.startswith('Change Request #'))

    def test_create_group_change_request(self):
        """Test creating a group change request."""
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': True,
            'group_kind_id': self.group_kind.id,
            'description': 'Test group create request',
        })
        
        self.assertEqual(change_request.is_group, True)
        self.assertEqual(change_request.group_kind_id, self.group_kind)
        self.assertIsNotNone(change_request.draft_record_id)

    def test_modify_change_request(self):
        """Test creating a modify change request."""
        change_request = self.env['change.request'].create({
            'type': 'modify',
            'partner_id': self.partner.id,
            'description': 'Test modify request',
        })
        
        self.assertEqual(change_request.type, 'modify')
        self.assertEqual(change_request.partner_id, self.partner)
        self.assertIsNotNone(change_request.draft_record_id)

    def test_delete_change_request(self):
        """Test creating a delete change request."""
        change_request = self.env['change.request'].create({
            'type': 'delete',
            'partner_id': self.partner.id,
            'description': 'Test delete request',
        })
        
        self.assertEqual(change_request.type, 'delete')
        self.assertEqual(change_request.partner_id, self.partner)
        self.assertIsNone(change_request.draft_record_id)

    def test_change_request_name_generation(self):
        """Test change request name generation."""
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': False,
            'description': 'Test name generation',
        })
        
        # Check initial name
        self.assertTrue(change_request.name.startswith('Change Request #'))
        
        # Update draft record name
        change_request.draft_record_id.write({'name': 'John Doe'})
        
        # Name should be updated
        self.assertIn('John Doe', change_request.name)

    def test_validation_constraints(self):
        """Test validation constraints."""
        # Test group kind required for group creation
        with self.assertRaises(ValidationError):
            self.env['change.request'].create({
                'type': 'create',
                'is_group': True,
                'description': 'Test without group kind',
            })
        
        # Test partner required for modify
        with self.assertRaises(ValidationError):
            self.env['change.request'].create({
                'type': 'modify',
                'description': 'Test modify without partner',
            })
        
        # Test partner required for delete
        with self.assertRaises(ValidationError):
            self.env['change.request'].create({
                'type': 'delete',
                'description': 'Test delete without partner',
            })

    def test_description_optional(self):
        """Test that description is optional."""
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': False,
        })
        
        self.assertIsNotNone(change_request.id)
        self.assertFalse(change_request.description)

    def test_description_validation_when_provided(self):
        """Test description validation when provided."""
        # Test short description
        with self.assertRaises(ValidationError):
            self.env['change.request'].create({
                'type': 'create',
                'is_group': False,
                'description': 'Short',
            })

    def test_duplicate_active_requests(self):
        """Test duplicate active requests constraint."""
        # Create first change request
        self.env['change.request'].create({
            'type': 'modify',
            'partner_id': self.partner.id,
            'description': 'First request',
        })
        
        # Should not allow second active request for same partner
        with self.assertRaises(ValidationError):
            self.env['change.request'].create({
                'type': 'modify',
                'partner_id': self.partner.id,
                'description': 'Second request',
            })

    def test_computed_fields(self):
        """Test computed fields."""
        change_request = self.env['change.request'].create({
            'type': 'modify',
            'partner_id': self.partner.id,
            'description': 'Test computed fields',
        })
        
        # Test partner name computation
        self.assertEqual(change_request.partner_name, self.partner.name)
        
        # Test draft fields computation
        # draft_name and draft_is_group fields have been removed as redundant

    def test_validation_summary(self):
        """Test validation summary computation."""
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': True,
            'group_kind_id': self.group_kind.id,
            'description': 'Valid description for testing',
        })
        
        # Should be valid
        self.assertEqual(change_request.validation_summary, 'Valid')
        self.assertFalse(change_request.has_validation_errors)
        
        # Test invalid case
        invalid_cr = self.env['change.request'].create({
            'type': 'create',
            'is_group': True,
            # Missing group_kind_id
            'description': 'Valid description',
        })
        
        self.assertIn('Group Kind is required', invalid_cr.validation_summary)
        self.assertTrue(invalid_cr.has_validation_errors)

    def test_can_submit_approve_reject(self):
        """Test can_submit, can_approve, can_reject fields."""
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': False,
            'description': 'Test workflow permissions',
        })
        
        # Initially can submit
        self.assertTrue(change_request.can_submit)
        self.assertFalse(change_request.can_approve)
        self.assertFalse(change_request.can_reject)
        
        # After submit
        change_request.action_submit()
        self.assertFalse(change_request.can_submit)
        self.assertTrue(change_request.can_approve)
        self.assertTrue(change_request.can_reject)
        
        # After approve
        change_request.action_approve()
        self.assertFalse(change_request.can_submit)
        self.assertFalse(change_request.can_approve)
        self.assertFalse(change_request.can_reject)
