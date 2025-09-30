# Technical Documentation - Change Management Module

## Architecture Overview

The Change Management module is built on top of Odoo's framework and integrates with the existing OpenG2P ecosystem. It follows a layered architecture with clear separation of concerns.

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Change Request Views  │  Partner Views  │  Wizard Views   │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Change Request Model  │  Partner Extensions  │  Workflows  │
├─────────────────────────────────────────────────────────────┤
│                    Data Access Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Draft Records  │  Partner Data  │  Group Memberships      │
├─────────────────────────────────────────────────────────────┤
│                    Integration Layer                        │
├─────────────────────────────────────────────────────────────┤
│  g2p_draft_publish  │  g2p_registry_base  │  g2p_social_registry │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### Change Request Model (`change.request`)

The central model that manages the change request lifecycle.

#### Fields
```python
# Basic Information
name = fields.Char('Change Request Name', required=True, default='New')
type = fields.Selection([
    ('create', 'Create'),
    ('modify', 'Modify'),
    ('delete', 'Delete')
], required=True, default='create')
state = fields.Selection([
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected')
], default='draft')

# Relationships
partner_id = fields.Many2one('res.partner', 'Partner')
draft_record_id = fields.Many2one('draft.record', 'Draft Record')
requester_id = fields.Many2one('res.users', 'Requester')
approver_id = fields.Many2one('res.users', 'Approver')

# Configuration
is_group = fields.Boolean('Is Group')
group_kind_id = fields.Many2one('g2p.group.kind', 'Group Kind')
description = fields.Text('Description')

# Computed Fields
partner_name = fields.Char('Partner Name', compute='_compute_partner_name')
draft_name = fields.Char('Draft Name', compute='_compute_draft_fields')
validation_summary = fields.Text('Validation Summary', compute='_compute_validation_summary')
can_submit = fields.Boolean('Can Submit', compute='_compute_can_submit')
can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')
can_reject = fields.Boolean('Can Reject', compute='_compute_can_reject')
```

#### Key Methods
```python
def create(self, vals):
    """Override create to set defaults and create draft record"""
    
def action_submit(self):
    """Submit change request for approval"""
    
def action_approve(self):
    """Approve change request and implement changes"""
    
def action_reject(self):
    """Reject change request"""
    
def _create_draft_record(self):
    """Create associated draft record"""
    
def _implement_changes(self):
    """Implement approved changes"""
```

### Partner Model Extensions (`res.partner`)

Extensions to the standard partner model for change management integration.

#### Additional Fields
```python
# Change Management Fields
change_request_ids = fields.One2many('change.request', 'partner_id', 'Change Requests')
has_active_draft = fields.Boolean('Has Active Draft', compute='_compute_has_active_draft')
active_change_request_id = fields.Many2one('change.request', 'Active Change Request', 
                                         compute='_compute_active_change_request', store=True)
draft_member_ids = fields.Many2many('draft.record', 'Draft Members', 
                                  compute='_compute_draft_members', store=False)
```

#### Key Methods
```python
def action_create_change_request(self):
    """Create change request from partner"""
    
def action_add_draft_members(self):
    """Add draft members to group"""
    
def write(self, vals):
    """Override write to prevent direct modification with active draft"""
    
def _validate_for_change_request(self):
    """Validate partner for change request creation"""
```

## Workflow Engine

### State Transitions

```
┌─────────┐    submit    ┌───────────┐    approve    ┌───────────┐
│  Draft  │ ──────────→ │ Submitted │ ────────────→ │ Approved  │
└─────────┘             └───────────┘               └───────────┘
     │                         │                           │
     │                         │ reject                    │
     │                         ↓                           │
     │                   ┌───────────┐                     │
     └─────────────────→ │ Rejected  │ ←───────────────────┘
                         └───────────┘
```

### Workflow Methods

#### Submit Workflow
```python
def action_submit(self):
    """Submit change request for approval"""
    # 1. Validate request
    self._validate_before_submit()
    
    # 2. Update state
    self.write({'state': 'submitted'})
    
    # 3. Create approval activity
    self._create_approval_activity()
    
    # 4. Update group member statuses
    self._update_group_member_statuses('submit')
    
    # 5. Log activity
    self.message_post(body="Change request submitted for approval")
```

#### Approval Workflow
```python
def action_approve(self):
    """Approve change request"""
    # 1. Validate approval
    self._validate_workflow_transition('approved')
    
    # 2. Update state
    self.write({'state': 'approved', 'approver_id': self.env.user.id})
    
    # 3. Implement changes
    self._implement_changes()
    
    # 4. Update group member statuses
    self._update_group_member_statuses('approve')
    
    # 5. Close activities
    self._close_related_activities()
    
    # 6. Send notifications
    self._send_approval_result_notification('approved')
```

## Integration Points

### Draft Publish Integration

The module integrates with `g2p_draft_publish` for data management:

```python
# Create draft record
draft_record = self.env['draft.record'].create({
    'name': f"New {'Group' if self.is_group else 'Individual'} - {self.id}",
    'is_group': self.is_group,
    'partner_data': json.dumps(partner_data)
})

# Publish draft record
created_partner = draft_record.action_publish()
```

### Registry Integration

Integration with OpenG2P registry modules:

```python
# Group kind selection
@api.onchange('is_group')
def _onchange_is_group(self):
    if self.is_group:
        group_kinds = self.env['g2p.group.kind'].search([])
        if len(group_kinds) == 1:
            self.group_kind_id = group_kinds[0].id
```

## Security Model

### Access Control

#### Model Access Rights
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_change_request_user,change.request.user,model_change_request,group_change_user,1,1,1,0
access_change_request_approver,change.request.approver,model_change_request,group_change_approver,1,1,1,1
access_change_request_admin,change.request.admin,model_change_request,group_change_admin,1,1,1,1
```

#### Record Rules
```xml
<record id="change_request_user_rule" model="ir.rule">
    <field name="name">Change Request: User Access</field>
    <field name="model_id" ref="model_change_request"/>
    <field name="domain_force">[('requester_id', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('group_change_user'))]"/>
</record>
```

### Security Groups

#### Change User Group
- Can create and manage their own change requests
- Can view their own change requests
- Cannot approve change requests

#### Change Approver Group
- Can view all change requests
- Can approve or reject change requests
- Can manage all change request states

#### Change Admin Group
- Full access to all change management features
- Can configure workflows and settings
- Can manage user permissions

## Data Validation

### Field Constraints

#### Change Request Constraints
```python
@api.constrains('is_group', 'group_kind_id')
def _check_group_kind_required_for_groups(self):
    """Group kind is required for group change requests"""
    for record in self:
        if record.is_group and not record.group_kind_id:
            raise ValidationError("Group Kind is required for group change requests")

@api.constrains('description')
def _check_description_length(self):
    """Description must meet minimum length if provided"""
    for record in self:
        if record.description and len(record.description.strip()) < 10:
            raise ValidationError("Description must be at least 10 characters long")
```

#### Partner Constraints
```python
@api.constrains('change_request_ids')
def _check_change_request_consistency(self):
    """Ensure change request consistency"""
    for partner in self:
        active_requests = partner.change_request_ids.filtered(
            lambda r: r.state in ['draft', 'submitted']
        )
        if len(active_requests) > 1:
            raise ValidationError("Only one active change request per partner is allowed")
```

## Performance Considerations

### Database Optimization

#### Indexes
```python
# Change request indexes
_index = [
    ('requester_id', 'state'),
    ('partner_id', 'state'),
    ('state', 'create_date'),
]

# Partner indexes
_index = [
    ('has_active_draft',),
    ('active_change_request_id',),
]
```

#### Query Optimization
```python
# Efficient partner lookup
partners_with_drafts = self.env['res.partner'].search([
    ('has_active_draft', '=', True)
])

# Efficient change request filtering
pending_requests = self.env['change.request'].search([
    ('state', '=', 'submitted'),
    ('create_date', '>=', date.today() - timedelta(days=30))
])
```

### Caching Strategy

#### Computed Fields
```python
# Store computed fields for performance
has_active_draft = fields.Boolean(compute='_compute_has_active_draft', store=True)
active_change_request_id = fields.Many2one(compute='_compute_active_change_request', store=True)
```

#### Search Methods
```python
def _search_active_change_request(self, operator, value):
    """Optimized search for active change requests"""
    if operator == '=' and value:
        return [('change_request_ids.state', 'in', ['draft', 'submitted'])]
    return []
```

## Error Handling

### Exception Types

#### Validation Errors
```python
from odoo.exceptions import ValidationError

# Field validation
if not self.group_kind_id and self.is_group:
    raise ValidationError("Group Kind is required for group change requests")

# Business rule validation
if self.state != 'draft':
    raise ValidationError("Can only submit draft change requests")
```

#### User Errors
```python
from odoo.exceptions import UserError

# Workflow errors
if not self.can_submit:
    raise UserError("Cannot submit this change request")

# Permission errors
if not self.env.user.has_group('g2p_change_management.group_change_approver'):
    raise UserError("Insufficient permissions to approve change requests")
```

### Error Recovery

#### Transaction Rollback
```python
@api.model
def create(self, vals):
    try:
        # Create change request
        change_request = super().create(vals)
        
        # Create draft record
        draft_record = change_request._create_draft_record()
        change_request.write({'draft_record_id': draft_record.id})
        
        return change_request
    except Exception as e:
        # Log error and re-raise
        _logger.error("Failed to create change request: %s", str(e))
        raise
```

## Testing Strategy

### Unit Tests
- Model method testing
- Field validation testing
- Constraint testing
- Computed field testing

### Integration Tests
- Workflow testing
- Cross-model interaction testing
- Draft publish integration testing
- Security testing

### Performance Tests
- Database query performance
- Large dataset handling
- Concurrent user testing
- Memory usage testing

## Deployment Considerations

### Database Migrations
- Schema changes
- Data migrations
- Index creation
- Constraint updates

### Configuration
- User group setup
- Permission configuration
- Workflow customization
- Notification settings

### Monitoring
- Error logging
- Performance metrics
- User activity tracking
- System health checks
