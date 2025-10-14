# API Documentation - Change Management Module

## Overview

This document provides comprehensive API documentation for the Change Management module, including model definitions, method signatures, and usage examples.

## Models

### Change Request Model (`change.request`)

The central model for managing change requests in the system.

#### Fields

##### Basic Information
```python
name = fields.Char(
    string='Change Request Name',
    required=True,
    default='New',
    help='Name of the change request'
)

type = fields.Selection([
    ('create', 'Create'),
    ('modify', 'Modify'),
    ('delete', 'Delete')
], string='Type', required=True, default='create',
   help='Type of change request')

state = fields.Selection([
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected')
], string='State', default='draft', readonly=True,
   help='Current state of the change request')

description = fields.Text(
    string='Description',
    help='Detailed description of the requested change'
)
```

##### Relationships
```python
partner_id = fields.Many2one(
    'res.partner',
    string='Partner',
    help='Partner associated with this change request'
)

draft_record_id = fields.Many2one(
    'draft.record',
    string='Draft Record',
    help='Draft record containing the changes'
)

requester_id = fields.Many2one(
    'res.users',
    string='Requester',
    default=lambda self: self.env.user,
    help='User who created this change request'
)

approver_id = fields.Many2one(
    'res.users',
    string='Approver',
    help='User who approved or rejected this change request'
)
```

##### Configuration
```python
is_group = fields.Boolean(
    string='Is Group',
    help='Whether this change request is for a group'
)

group_kind_id = fields.Many2one(
    'g2p.group.kind',
    string='Group Kind',
    help='Type of group for group change requests'
)
```

##### Computed Fields
```python
partner_name = fields.Char(
    string='Partner Name',
    compute='_compute_partner_name',
    help='Name of the associated partner'
)

draft_name = fields.Char(
    string='Draft Name',
    compute='_compute_draft_fields',
    help='Name of the associated draft record'
)

validation_summary = fields.Text(
    string='Validation Summary',
    compute='_compute_validation_summary',
    help='Summary of validation status'
)

can_submit = fields.Boolean(
    string='Can Submit',
    compute='_compute_can_submit',
    help='Whether this change request can be submitted'
)

can_approve = fields.Boolean(
    string='Can Approve',
    compute='_compute_can_approve',
    help='Whether this change request can be approved'
)

can_reject = fields.Boolean(
    string='Can Reject',
    compute='_compute_can_reject',
    help='Whether this change request can be rejected'
)
```

#### Methods

##### Core Methods
```python
@api.model
def create(self, vals):
    """
    Create a new change request with default values and draft record.
    
    Args:
        vals (dict): Values for creating the change request
        
    Returns:
        change.request: The created change request
        
    Raises:
        ValidationError: If validation fails
    """
    
def action_submit(self):
    """
    Submit the change request for approval.
    
    Raises:
        ValidationError: If validation fails
        UserError: If insufficient permissions
    """
    
def action_approve(self):
    """
    Approve the change request and implement changes.
    
    Raises:
        ValidationError: If validation fails
        UserError: If insufficient permissions
    """
    
def action_reject(self):
    """
    Reject the change request.
    
    Raises:
        ValidationError: If validation fails
        UserError: If insufficient permissions
    """
```

##### Helper Methods
```python
def _create_draft_record(self):
    """
    Create an associated draft record for this change request.
    
    Returns:
        draft.record: The created draft record
    """
    
def _implement_changes(self):
    """
    Implement the approved changes.
    
    For create requests: Creates new partner
    For modify requests: Updates existing partner
    For delete requests: Deactivates partner
    """
    
def _update_change_request_name(self):
    """
    Update the change request name based on partner or draft record.
    """
    
def _validate_before_submit(self):
    """
    Validate the change request before submission.
    
    Raises:
        ValidationError: If validation fails
    """
    
def _create_approval_activity(self):
    """
    Create an approval activity for the change request.
    """
    
def _update_group_member_statuses(self, action_type):
    """
    Update the status of group members based on the action.
    
    Args:
        action_type (str): Type of action (submit, approve, reject)
    """
```

##### Validation Methods
```python
@api.constrains('is_group', 'group_kind_id')
def _check_group_kind_required_for_groups(self):
    """Validate that group kind is required for group requests."""
    
@api.constrains('description')
def _check_description_length(self):
    """Validate description length if provided."""
    
@api.constrains('partner_id', 'type')
def _check_partner_consistency(self):
    """Validate partner consistency based on request type."""
    
@api.constrains('state')
def _check_state_transitions(self):
    """Validate state transitions."""
    
@api.constrains('name')
def _check_name_unique(self):
    """Validate that change request names are unique."""
    
@api.constrains('partner_id')
def _check_duplicate_active_requests(self):
    """Validate no duplicate active requests for same partner."""
```

### Partner Model Extensions (`res.partner`)

Extensions to the standard partner model for change management integration.

#### Additional Fields
```python
change_request_ids = fields.One2many(
    'change.request',
    'partner_id',
    string='Change Requests',
    help='All change requests for this partner'
)

has_active_draft = fields.Boolean(
    string='Has Active Draft',
    compute='_compute_has_active_draft',
    help='Whether this partner has an active change request'
)

active_change_request_id = fields.Many2one(
    'change.request',
    string='Active Change Request',
    compute='_compute_active_change_request',
    store=True,
    search='_search_active_change_request',
    help='Currently active change request for this partner'
)

draft_member_ids = fields.Many2many(
    'draft.record',
    string='Draft Members',
    compute='_compute_draft_members',
    store=False,
    help='Draft members for group partners'
)
```

#### Methods
```python
def action_create_change_request(self):
    """
    Create a new change request for this partner.
    
    Returns:
        dict: Action to open the change request form
    """
    
def action_add_draft_members(self):
    """
    Open the wizard to add draft members to this group.
    
    Returns:
        dict: Action to open the draft member wizard
        
    Raises:
        UserError: If partner is not a group or has no active change request
    """
    
def _create_draft_from_partner(self):
    """
    Create a draft record from this partner's data.
    
    Returns:
        draft.record: The created draft record
    """
    
def _validate_for_change_request(self):
    """
    Validate this partner for change request creation.
    
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    
@api.constrains('change_request_ids')
def _check_change_request_consistency(self):
    """Validate change request consistency."""
    
@api.constrains('active')
def _check_active_with_change_requests(self):
    """Validate partner can be deactivated with active change requests."""
```

## Wizards

### Group Member Confirmation Wizard (`group.member.confirmation.wizard`)

Wizard for confirming group member status updates.

#### Fields
```python
change_request_id = fields.Many2one(
    'change.request',
    string='Change Request',
    required=True
)

action_type = fields.Selection([
    ('submit', 'Submit'),
    ('approve', 'Approve'),
    ('reject', 'Reject')
], string='Action Type', required=True)

member_count = fields.Integer(
    string='Member Count',
    readonly=True
)

member_names = fields.Text(
    string='Member Names',
    readonly=True
)

confirmation_message = fields.Text(
    string='Confirmation Message',
    readonly=True
)
```

#### Methods
```python
@api.model
def default_get(self, fields_list):
    """
    Set default values for the wizard.
    
    Args:
        fields_list (list): List of field names
        
    Returns:
        dict: Default values
    """
    
def action_confirm(self):
    """
    Confirm the action and update member statuses.
    
    Returns:
        dict: Action to close the wizard
    """
    
def action_cancel(self):
    """
    Cancel the action.
    
    Returns:
        dict: Action to close the wizard
    """
```

## Usage Examples

### Creating a Change Request

#### Basic Create Request
```python
# Create a new individual change request
change_request = env['change.request'].create({
    'type': 'create',
    'is_group': False,
    'description': 'Add new individual registrant'
})

# The draft record is automatically created
draft_record = change_request.draft_record_id

# Update the draft record with data
draft_record.write({
    'name': 'John Doe',
    'given_name': 'John',
    'family_name': 'Doe',
    'phone': '1234567890'
})

# Submit for approval
change_request.action_submit()
```

#### Group Create Request
```python
# Create a new group change request
group_kind = env['g2p.group.kind'].search([], limit=1)
change_request = env['change.request'].create({
    'type': 'create',
    'is_group': True,
    'group_kind_id': group_kind.id,
    'description': 'Add new group registrant'
})

# Update the draft record
draft_record = change_request.draft_record_id
draft_record.write({
    'name': 'Doe Family',
    'phone': '0987654321'
})

# Submit for approval
change_request.action_submit()
```

#### Modify Request
```python
# Create a modify request for existing partner
partner = env['res.partner'].search([('is_registrant', '=', True)], limit=1)
change_request = env['change.request'].create({
    'type': 'modify',
    'partner_id': partner.id,
    'description': 'Update partner phone number'
})

# Update the draft record
draft_record = change_request.draft_record_id
draft_record.write({
    'phone': '5555555555'
})

# Submit for approval
change_request.action_submit()
```

#### Delete Request
```python
# Create a delete request
partner = env['res.partner'].search([('is_registrant', '=', True)], limit=1)
change_request = env['change.request'].create({
    'type': 'delete',
    'partner_id': partner.id,
    'description': 'Remove partner from registry'
})

# Submit for approval
change_request.action_submit()
```

### Approval Process

#### Approving a Change Request
```python
# Find submitted change requests
submitted_requests = env['change.request'].search([
    ('state', '=', 'submitted')
])

# Approve a change request
change_request = submitted_requests[0]
change_request.action_approve()

# The changes are automatically implemented
if change_request.type == 'create':
    new_partner = change_request.partner_id
    print(f"Created new partner: {new_partner.name}")
elif change_request.type == 'modify':
    updated_partner = change_request.partner_id
    print(f"Updated partner: {updated_partner.name}")
elif change_request.type == 'delete':
    deactivated_partner = change_request.partner_id
    print(f"Deactivated partner: {deactivated_partner.name}")
```

#### Rejecting a Change Request
```python
# Reject a change request
change_request.action_reject()

# The change request is marked as rejected
print(f"Change request state: {change_request.state}")
```

### Managing Group Members

#### Adding Draft Members
```python
# Get a group partner with active change request
group = env['res.partner'].search([
    ('is_group', '=', True),
    ('has_active_draft', '=', True)
], limit=1)

# Open the draft member wizard
action = group.action_add_draft_members()
wizard = env['draft.group.add.members.wizard'].create({
    'change_request_id': group.active_change_request_id.id
})

# Add draft members
draft_members = env['draft.record'].search([
    ('is_group', '=', False),
    ('state', 'in', ['draft', 'submitted']
)], limit=3)

wizard.write({
    'selected_member_ids': [(6, 0, draft_members.ids)]
})

# Save the members
wizard.action_save_members()
```

### Querying Change Requests

#### Basic Queries
```python
# Get all change requests
all_requests = env['change.request'].search([])

# Get change requests by state
draft_requests = env['change.request'].search([
    ('state', '=', 'draft')
])

submitted_requests = env['change.request'].search([
    ('state', '=', 'submitted')
])

# Get change requests by type
create_requests = env['change.request'].search([
    ('type', '=', 'create')
])

modify_requests = env['change.request'].search([
    ('type', '=', 'modify')
])

delete_requests = env['change.request'].search([
    ('type', '=', 'delete')
])
```

#### Advanced Queries
```python
# Get change requests by requester
user_requests = env['change.request'].search([
    ('requester_id', '=', env.user.id)
])

# Get change requests by partner
partner_requests = env['change.request'].search([
    ('partner_id', '=', partner.id)
])

# Get change requests by date range
from datetime import datetime, timedelta
start_date = datetime.now() - timedelta(days=30)
recent_requests = env['change.request'].search([
    ('create_date', '>=', start_date)
])

# Get group change requests
group_requests = env['change.request'].search([
    ('is_group', '=', True)
])
```

### Partner Extensions

#### Checking Active Drafts
```python
# Check if partner has active draft
if partner.has_active_draft:
    print(f"Partner {partner.name} has an active change request")
    active_cr = partner.active_change_request_id
    print(f"Active change request: {active_cr.name}")
else:
    print(f"Partner {partner.name} has no active change requests")
```

#### Creating Change Request from Partner
```python
# Create change request from partner
action = partner.action_create_change_request()
change_request = env['change.request'].create({
    'type': 'modify',
    'partner_id': partner.id,
    'description': 'Update partner information'
})
```

## Error Handling

### Common Exceptions

#### ValidationError
```python
from odoo.exceptions import ValidationError

try:
    change_request = env['change.request'].create({
        'type': 'create',
        'is_group': True,
        # Missing group_kind_id
    })
except ValidationError as e:
    print(f"Validation error: {e}")
```

#### UserError
```python
from odoo.exceptions import UserError

try:
    change_request.action_approve()
except UserError as e:
    print(f"User error: {e}")
```

### Error Recovery

#### Transaction Rollback
```python
try:
    with env.cr.savepoint():
        change_request = env['change.request'].create(vals)
        draft_record = change_request._create_draft_record()
        change_request.write({'draft_record_id': draft_record.id})
except Exception as e:
    # Transaction is automatically rolled back
    print(f"Error occurred: {e}")
```

## Security Considerations

### Access Control
```python
# Check user permissions
if not env.user.has_group('g2p_change_management.group_change_approver'):
    raise UserError("Insufficient permissions to approve change requests")

# Use with_user for different user context
change_request = env['change.request'].with_user(user).create(vals)
```

### Data Validation
```python
# Validate before operations
change_request._validate_before_submit()

# Check constraints
change_request._check_group_kind_required_for_groups()
change_request._check_description_length()
```

## Performance Tips

### Efficient Queries
```python
# Use search with proper domains
efficient_search = env['change.request'].search([
    ('state', '=', 'submitted'),
    ('create_date', '>=', start_date)
], limit=100)

# Use read() for specific fields
field_data = env['change.request'].search([]).read(['name', 'state', 'type'])

# Use browse() for existing records
change_request = env['change.request'].browse(record_id)
```

### Batch Operations
```python
# Batch create
vals_list = [
    {'type': 'create', 'is_group': False, 'description': f'Request {i}'}
    for i in range(10)
]
change_requests = env['change.request'].create(vals_list)

# Batch update
change_requests.write({'state': 'submitted'})
```

## Testing

### Unit Tests
```python
from odoo.tests.common import TransactionCase

class TestChangeRequest(TransactionCase):
    def test_create_change_request(self):
        change_request = self.env['change.request'].create({
            'type': 'create',
            'is_group': False,
            'description': 'Test request'
        })
        self.assertEqual(change_request.state, 'draft')
        self.assertIsNotNone(change_request.draft_record_id)
```

### Integration Tests
```python
def test_workflow(self):
    change_request = self.env['change.request'].create({
        'type': 'create',
        'is_group': False,
        'description': 'Test workflow'
    })
    
    # Submit
    change_request.action_submit()
    self.assertEqual(change_request.state, 'submitted')
    
    # Approve
    change_request.action_approve()
    self.assertEqual(change_request.state, 'approved')
    self.assertIsNotNone(change_request.partner_id)
```
