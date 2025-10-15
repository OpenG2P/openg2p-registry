# Configuration Guide - Change Management Module

## Table of Contents

1. [Installation Requirements](#installation-requirements)
2. [User Groups Setup](#user-groups-setup)
3. [Permissions Configuration](#permissions-configuration)
4. [Workflow Configuration](#workflow-configuration)
5. [Notification Settings](#notification-settings)
6. [Customization Options](#customization-options)
7. [Troubleshooting](#troubleshooting)

## Installation Requirements

### Prerequisites

Before installing the Change Management module, ensure the following modules are installed:

#### Core OpenG2P Modules

- `g2p_registry_base` - Base registry functionality
- `g2p_registry_group` - Group management
- `g2p_registry_individual` - Individual management
- `g2p_registry_membership` - Membership management
- `g2p_social_registry` - Social registry functionality
- `g2p_social_registry_theme` - UI theme
- `g2p_draft_publish` - Draft record management

#### Optional Modules

- `g2p_registry_g2p_connect_rest_api` - REST API integration
- `g2p_social_registry_dashboard` - Dashboard functionality

### Installation Steps

1. **Install Prerequisites**

   ```bash
   # Install required modules
   odoo-bin -d your_database -i g2p_registry_base,g2p_registry_group,g2p_registry_individual,g2p_registry_membership,g2p_social_registry,g2p_social_registry_theme,g2p_draft_publish
   ```

2. **Install Change Management Module**

   ```bash
   # Install the change management module
   odoo-bin -d your_database -i g2p_change_management
   ```

3. **Update Module List**
   ```bash
   # Update the module list
   odoo-bin -d your_database -u all
   ```

## User Groups Setup

### Default Security Groups

The module creates three default security groups:

#### Change User Group (`group_change_user`)

- **Purpose**: Basic users who can create and manage their own change requests
- **Permissions**:
  - Create change requests
  - View their own change requests
  - Edit their own change requests (in draft state)
  - Submit change requests for approval
  - Cannot approve or reject change requests

#### Change Approver Group (`group_change_approver`)

- **Purpose**: Users who can approve or reject change requests
- **Permissions**:
  - View all change requests
  - Approve or reject change requests
  - Manage change request states
  - View all partner records
  - Cannot create change requests (unless also in user group)

#### Change Admin Group (`group_change_admin`)

- **Purpose**: Administrators with full access
- **Permissions**:
  - All permissions from user and approver groups
  - Create, edit, and delete change requests
  - Manage all change request states
  - Configure workflows and settings
  - Manage user permissions

### Setting Up User Groups

#### Step 1: Access User Groups

1. **Navigate** to Settings → Users & Companies → Groups
2. **Search** for "Change Management" groups
3. **Verify** the groups are created correctly

#### Step 2: Assign Users to Groups

1. **Navigate** to Settings → Users & Companies → Users
2. **Select** a user to configure
3. **Go** to the "Access Rights" tab
4. **Add** the appropriate change management groups
5. **Save** the user configuration

#### Step 3: Verify Group Permissions

1. **Check** that users can access the Change Management menu
2. **Test** that permissions are working correctly
3. **Adjust** group memberships as needed

## Permissions Configuration

### Model Access Rights

The module defines access rights for the following models:

#### Change Request Model

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_change_request_user,change.request.user,model_change_request,group_change_user,1,1,1,0
access_change_request_approver,change.request.approver,model_change_request,group_change_approver,1,1,1,1
access_change_request_admin,change.request.admin,model_change_request,group_change_admin,1,1,1,1
```

#### Draft Record Model

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_draft_record_user,draft.record.user,model_draft_record,group_change_user,1,1,1,0
access_draft_record_approver,draft.record.approver,model_draft_record,group_change_approver,1,1,1,1
access_draft_record_admin,draft.record.admin,model_draft_record,group_change_admin,1,1,1,1
```

#### Group Member Confirmation Wizard

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_group_member_confirmation_wizard_user,group.member.confirmation.wizard.user,model_group_member_confirmation_wizard,group_change_user,1,1,1,0
access_group_member_confirmation_wizard_approver,group.member.confirmation.wizard.approver,model_group_member_confirmation_wizard,group_change_approver,1,1,1,1
access_group_member_confirmation_wizard_admin,group.member.confirmation.wizard.admin,model_group_member_confirmation_wizard,group_change_admin,1,1,1,1
```

### Record Rules

#### Change Request User Rule

```xml
<record id="change_request_user_rule" model="ir.rule">
    <field name="name">Change Request: User Access</field>
    <field name="model_id" ref="model_change_request" />
    <field name="domain_force">[('requester_id', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('group_change_user'))]" />
</record>
```

#### Change Request Approver Rule

```xml
<record id="change_request_approver_rule" model="ir.rule">
    <field name="name">Change Request: Approver Access</field>
    <field name="model_id" ref="model_change_request" />
    <field name="domain_force">[(1, '=', 1)]</field>
    <field name="groups" eval="[(4, ref('group_change_approver'))]" />
</record>
```

### Customizing Permissions

#### Adding Custom Access Rights

1. **Create** a new access right record
2. **Define** the model and group
3. **Set** the appropriate permissions
4. **Update** the module

#### Modifying Record Rules

1. **Access** the record rules configuration
2. **Modify** the domain conditions
3. **Test** the changes
4. **Deploy** the updated configuration

## Workflow Configuration

### Default Workflow States

The module uses a four-state workflow:

1. **Draft** - Initial state when change request is created
2. **Submitted** - State when change request is submitted for approval
3. **Approved** - State when change request is approved
4. **Rejected** - State when change request is rejected

### Workflow Transitions

#### Allowed Transitions

- Draft → Submitted (via `action_submit()`)
- Submitted → Approved (via `action_approve()`)
- Submitted → Rejected (via `action_reject()`)

#### Restricted Transitions

- No transitions from Approved or Rejected states
- No direct transitions from Draft to Approved/Rejected

### Customizing Workflow

#### Adding New States

1. **Modify** the `state` field selection
2. **Update** the workflow methods
3. **Add** new transition methods
4. **Update** the UI views

#### Adding New Transitions

1. **Create** new action methods
2. **Update** the workflow validation
3. **Modify** the UI buttons
4. **Test** the new transitions

### Workflow Validation

#### Pre-submit Validation

- Description length (if provided)
- Required fields validation
- Business rule validation

#### Pre-approval Validation

- Workflow state validation
- Permission validation
- Data consistency validation

## Notification Settings

### Email Notifications

The module sends email notifications for workflow events:

#### Submission Notifications

- **Recipients**: Approvers
- **Content**: Change request details and submission information
- **Template**: Customizable email template

#### Approval Notifications

- **Recipients**: Requester
- **Content**: Approval confirmation and implementation details
- **Template**: Customizable email template

#### Rejection Notifications

- **Recipients**: Requester
- **Content**: Rejection reason and next steps
- **Template**: Customizable email template

### Configuring Notifications

#### Step 1: Access Email Templates

1. **Navigate** to Settings → Technical → Email → Templates
2. **Search** for "Change Management" templates
3. **Review** the existing templates

#### Step 2: Customize Templates

1. **Select** a template to modify
2. **Edit** the subject and body
3. **Add** custom fields and logic
4. **Save** the template

#### Step 3: Configure Recipients

1. **Modify** the notification methods
2. **Set** the appropriate recipients
3. **Test** the notification system

### Activity Notifications

#### Approval Activities

- **Type**: To Do
- **Assigned to**: Approvers
- **Deadline**: Configurable (default 7 days)
- **Description**: Change request details

#### Configuring Activities

1. **Access** the activity configuration
2. **Set** the default deadline
3. **Configure** the activity type
4. **Test** the activity creation

## Customization Options

### UI Customization

#### View Customization

1. **Access** the view definitions
2. **Modify** the XML views
3. **Add** custom fields or buttons
4. **Update** the module

#### Menu Customization

1. **Modify** the menu structure
2. **Add** custom menu items
3. **Configure** menu permissions
4. **Test** the menu changes

### Field Customization

#### Adding Custom Fields

1. **Extend** the change request model
2. **Add** the new fields
3. **Update** the views
4. **Add** validation if needed

#### Modifying Existing Fields

1. **Override** the field definitions
2. **Update** the validation logic
3. **Modify** the UI components
4. **Test** the changes

### Business Logic Customization

#### Adding Custom Validation

1. **Create** new constraint methods
2. **Add** the constraints to the model
3. **Test** the validation logic
4. **Deploy** the changes

#### Modifying Workflow Logic

1. **Override** the workflow methods
2. **Add** custom business logic
3. **Update** the validation
4. **Test** the workflow changes

## Troubleshooting

### Common Configuration Issues

#### Permission Issues

**Problem**: Users cannot access change management features **Solution**:

1. Check user group assignments
2. Verify access rights configuration
3. Review record rules
4. Test with different users

#### Workflow Issues

**Problem**: Workflow transitions not working **Solution**:

1. Check workflow state definitions
2. Verify transition methods
3. Review validation logic
4. Test with different scenarios

#### Notification Issues

**Problem**: Email notifications not being sent **Solution**:

1. Check email configuration
2. Verify notification templates
3. Review recipient settings
4. Test email functionality

### Debugging Configuration

#### Enable Debug Mode

1. **Navigate** to Settings → Developer Tools
2. **Enable** debug mode
3. **Access** additional configuration options
4. **Review** system logs

#### Check System Logs

1. **Access** the system logs
2. **Look** for error messages
3. **Review** the stack traces
4. **Identify** the root cause

#### Test Configuration

1. **Create** test change requests
2. **Test** the workflow transitions
3. **Verify** the permissions
4. **Check** the notifications

### Performance Optimization

#### Database Optimization

1. **Add** appropriate indexes
2. **Optimize** query performance
3. **Review** database constraints
4. **Monitor** system performance

#### Caching Configuration

1. **Enable** appropriate caching
2. **Configure** cache settings
3. **Monitor** cache performance
4. **Adjust** cache parameters

## Maintenance

### Regular Maintenance Tasks

#### User Management

1. **Review** user group assignments
2. **Update** user permissions
3. **Remove** inactive users
4. **Audit** access rights

#### Workflow Monitoring

1. **Monitor** workflow performance
2. **Review** approval times
3. **Identify** bottlenecks
4. **Optimize** processes

#### Data Cleanup

1. **Archive** old change requests
2. **Clean** up draft records
3. **Remove** duplicate data
4. **Maintain** data integrity

### Backup and Recovery

#### Configuration Backup

1. **Export** user groups and permissions
2. **Backup** workflow configurations
3. **Save** notification templates
4. **Document** customizations

#### Recovery Procedures

1. **Restore** from backups
2. **Verify** configuration integrity
3. **Test** system functionality
4. **Update** documentation

## Security Considerations

### Access Control

1. **Implement** principle of least privilege
2. **Regularly** review user permissions
3. **Monitor** access patterns
4. **Audit** security events

### Data Protection

1. **Encrypt** sensitive data
2. **Implement** data retention policies
3. **Monitor** data access
4. **Comply** with privacy regulations

### System Security

1. **Keep** the system updated
2. **Monitor** security vulnerabilities
3. **Implement** security best practices
4. **Regularly** audit the system
