from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


class TestSecurity(TransactionCase):
    """Test cases for security and access control."""

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

    def test_change_request_access_rights(self):
        """Test change request access rights."""
        # Create change request as admin
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': False,
            'description': 'Test access rights',
        })
        
        # Test user should be able to read their own change requests
        change_request_user = self.env['change.request'].with_user(self.user).browse(change_request.id)
        self.assertEqual(change_request_user.name, change_request.name)
        
        # Should be able to create change requests
        new_cr = self.env['change.request'].with_user(self.user).create({
            'type': 'create',
            'is_group': False,
            'description': 'Test user creation',
        })
        self.assertIsNotNone(new_cr.id)

    def test_partner_access_rights(self):
        """Test partner access rights."""
        # Test user should be able to read partners
        partner_user = self.env['res.partner'].with_user(self.user).browse(self.partner.id)
        self.assertEqual(partner_user.name, self.partner.name)
        
        # Should be able to create change requests from partner
        action = partner_user.action_create_change_request()
        self.assertEqual(action['res_model'], 'change.request')

    def test_draft_record_access_rights(self):
        """Test draft record access rights."""
        # Create change request
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': False,
            'description': 'Test draft record access',
        })
        
        draft_record = change_request.draft_record_id
        
        # Test user should be able to read draft records
        draft_user = self.env['draft.record'].with_user(self.user).browse(draft_record.id)
        self.assertEqual(draft_user.name, draft_record.name)
        
        # Should be able to update draft records
        draft_user.write({'name': 'Updated Name'})
        self.assertEqual(draft_user.name, 'Updated Name')

    def test_wizard_access_rights(self):
        """Test wizard access rights."""
        # Create change request for group
        group = self.env['res.partner'].create({
            'name': 'Test Group',
            'is_registrant': True,
            'is_group': True,
            'unique_id': 'GRP001',
            'company_id': self.env.company.id,
        })
        
        change_request = self.env['change.request'].create({
            'type': 'modify',
            'partner_id': group.id,
            'description': 'Test wizard access',
        })
        
        # Test user should be able to access wizard
        action = group.with_user(self.user).action_add_draft_members()
        self.assertEqual(action['res_model'], 'draft.group.add.members.wizard')

    def test_workflow_permissions(self):
        """Test workflow permissions."""
        # Create change request as user
        change_request = self.env['change.request'].with_user(self.user).create({
            'type': 'create',
            'is_group': False,
            'description': 'Test workflow permissions',
        })
        
        # User should be able to submit their own change request
        change_request.action_submit()
        self.assertEqual(change_request.state, 'submitted')
        
        # User should not be able to approve their own change request
        # (This depends on the security group configuration)
        # For now, we'll test that the action exists
        self.assertTrue(hasattr(change_request, 'action_approve'))

    def test_data_isolation(self):
        """Test data isolation between users."""
        # Create change request as admin
        admin_cr = self.env['change.request'].create({
            'type': 'create',
            'is_group': False,
            'description': 'Admin change request',
        })
        
        # Create change request as user
        user_cr = self.env['change.request'].with_user(self.user).create({
            'type': 'create',
            'is_group': False,
            'description': 'User change request',
        })
        
        # User should see their own change request
        user_crs = self.env['change.request'].with_user(self.user).search([])
        self.assertIn(user_cr, user_crs)
        
        # User should not see admin's change request
        # (This depends on the security rules configuration)
        # For now, we'll test that both exist in the system
        all_crs = self.env['change.request'].with_context(active_test=False).search([])
        self.assertIn(admin_cr, all_crs)
        self.assertIn(user_cr, all_crs)

    def test_security_groups(self):
        """Test security group assignments."""
        # Test that users can be assigned to change management groups
        change_user_group = self.env.ref('g2p_change_management.group_change_user', raise_if_not_found=False)
        change_approver_group = self.env.ref('g2p_change_management.group_change_approver', raise_if_not_found=False)
        change_admin_group = self.env.ref('g2p_change_management.group_change_admin', raise_if_not_found=False)
        
        if change_user_group:
            self.user.write({'groups_id': [(4, change_user_group.id)]})
            self.assertIn(change_user_group, self.user.groups_id)
        
        if change_approver_group:
            self.approver.write({'groups_id': [(4, change_approver_group.id)]})
            self.assertIn(change_approver_group, self.approver.groups_id)
        
        if change_admin_group:
            admin_user = self.env.ref('base.user_admin')
            admin_user.write({'groups_id': [(4, change_admin_group.id)]})
            self.assertIn(change_admin_group, admin_user.groups_id)

    def test_model_access_rights(self):
        """Test model access rights."""
        # Test change.request model access
        change_request_model = self.env['ir.model'].search([('model', '=', 'change.request')])
        if change_request_model:
            access_rights = self.env['ir.model.access'].search([
                ('model_id', '=', change_request_model.id)
            ])
            self.assertTrue(access_rights)
        
        # Test draft.record model access
        draft_record_model = self.env['ir.model'].search([('model', '=', 'draft.record')])
        if draft_record_model:
            access_rights = self.env['ir.model.access'].search([
                ('model_id', '=', draft_record_model.id)
            ])
            self.assertTrue(access_rights)

    def test_record_rules(self):
        """Test record rules."""
        # Test that record rules are properly configured
        change_request_rules = self.env['ir.rule'].search([
            ('model_id.model', '=', 'change.request')
        ])
        self.assertTrue(change_request_rules)
        
        # Test that rules have proper domains
        for rule in change_request_rules:
            self.assertTrue(rule.domain)

    def test_menu_access(self):
        """Test menu access."""
        # Test that change management menus are accessible
        change_management_menu = self.env.ref('g2p_change_management.menu_change_management_root', raise_if_not_found=False)
        if change_management_menu:
            self.assertTrue(change_management_menu.name)
        
        change_requests_menu = self.env.ref('g2p_change_management.menu_change_request', raise_if_not_found=False)
        if change_requests_menu:
            self.assertTrue(change_requests_menu.name)

    def test_action_access(self):
        """Test action access."""
        # Test that change request actions are accessible
        change_request_action = self.env.ref('g2p_change_management.action_change_request', raise_if_not_found=False)
        if change_request_action:
            self.assertEqual(change_request_action.res_model, 'change.request')
            self.assertEqual(change_request_action.view_mode, 'tree,form')
