# User Guide - Change Management Module

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Change Requests](#creating-change-requests)
3. [Managing Group Members](#managing-group-members)
4. [Approval Process](#approval-process)
5. [Viewing and Tracking](#viewing-and-tracking)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Getting Started

### What is Change Management?

The Change Management module allows you to:

- **Create** new individuals or groups in the registry
- **Modify** existing registrant information
- **Delete** registrants from the registry
- **Manage** group memberships
- **Track** all changes through an approval workflow

### Accessing Change Management

1. **Navigate** to the main menu
2. **Click** on "Change Management"
3. **Select** "Change Requests" to view all requests
4. **Click** "Create" to start a new change request

### User Roles

#### Change User

- Can create and manage their own change requests
- Can view their own change requests
- Cannot approve change requests

#### Change Approver

- Can view all change requests
- Can approve or reject change requests
- Can manage all change request states

#### Change Admin

- Full access to all change management features
- Can configure workflows and settings
- Can manage user permissions

## Creating Change Requests

### Step 1: Choose Request Type

When creating a new change request, you'll need to select the type:

#### Create Request

- **Purpose**: Add a new individual or group to the registry
- **Use Case**: New registrants joining the program
- **Required Fields**:
  - Type: "Create"
  - Is Group: Yes/No
  - Group Kind (if creating a group)
  - Description (optional but recommended)

#### Modify Request

- **Purpose**: Update existing registrant information
- **Use Case**: Change of address, phone number, or other details
- **Required Fields**:
  - Type: "Modify"
  - Partner: Select existing registrant
  - Description: Explain what changes are needed

#### Delete Request

- **Purpose**: Remove a registrant from the registry
- **Use Case**: Registrant no longer eligible or deceased
- **Required Fields**:
  - Type: "Delete"
  - Partner: Select existing registrant
  - Description: Reason for deletion

### Step 2: Fill in Details

#### Basic Information

- **Name**: Automatically generated based on registrant name
- **Type**: Create, Modify, or Delete
- **Description**: Detailed explanation of the change
- **Requester**: Automatically set to current user
- **Approver**: Set when request is approved

#### Partner Information (for Modify/Delete)

- **Partner**: Select the existing registrant
- **Partner Name**: Display name of the registrant
- **Is Group**: Whether the registrant is a group

#### Draft Record (for Create/Modify)

- **Draft Name**: Name of the draft record
- **Is Group**: Whether creating a group or individual
- **Group Kind**: Type of group (for group creation)

### Step 3: Save and Submit

1. **Click** "Save" to save your changes
2. **Review** the information for accuracy
3. **Click** "Submit" to send for approval
4. **Confirm** submission in the dialog

## Managing Group Members

### Adding Draft Members to Groups

When working with group change requests, you can manage individual members:

#### Step 1: Access Draft Members

1. **Open** the group registrant
2. **Navigate** to the "Draft Members" tab
3. **Click** "Add Draft Members"

#### Step 2: Select Members

1. **Browse** available draft individuals
2. **Select** individuals to add to the group
3. **Review** the selection
4. **Click** "Save Members"

#### Step 3: Manage Members

- **View** current draft members
- **Remove** members if needed
- **Update** member information
- **Submit** changes for approval

### Member Status Updates

When a group change request is submitted, approved, or rejected:

- **Draft members** are automatically updated with the same status
- **Confirmation dialog** shows which members will be affected
- **Status changes** are logged for audit purposes

## Approval Process

### For Approvers

#### Step 1: Review Submitted Requests

1. **Navigate** to Change Management → Change Requests
2. **Filter** by "Submitted" status
3. **Review** request details and draft data
4. **Validate** information accuracy

#### Step 2: Make Decision

1. **Click** "Approve" to approve the request
2. **OR** click "Reject" to reject the request
3. **Add** comments if needed
4. **Confirm** your decision

#### Step 3: Monitor Implementation

- **Approved requests** are automatically implemented
- **New partners** are created for "Create" requests
- **Existing partners** are updated for "Modify" requests
- **Partners** are deactivated for "Delete" requests

### For Requesters

#### Step 1: Track Your Requests

1. **Navigate** to Change Management → Change Requests
2. **Filter** by "My Requests" or your name
3. **View** status of your requests
4. **Check** for any required actions

#### Step 2: Handle Rejections

1. **Review** rejection reason
2. **Make** necessary corrections
3. **Resubmit** the request
4. **Contact** approver if clarification needed

## Viewing and Tracking

### Change Request List View

The main list view shows:

- **Name**: Change request name
- **Type**: Create, Modify, or Delete
- **Partner**: Related registrant
- **State**: Draft, Submitted, Approved, or Rejected
- **Requester**: Who created the request
- **Approver**: Who approved/rejected (if applicable)
- **Create Date**: When the request was created
- **Last Update**: When the request was last modified

### Change Request Form View

The form view provides:

- **Complete request details**
- **Draft record information**
- **Workflow status and actions**
- **Message history and comments**
- **Related activities and tasks**

### Partner View Extensions

When viewing a partner record:

- **Change Request History**: All related change requests
- **Active Draft Warning**: Alert if partner has pending changes
- **Draft Members Tab**: For group partners with draft members
- **Add Draft Members Button**: To add new draft members

### Dashboard Integration

The dashboard shows:

- **Pending Approvals**: Requests awaiting your approval
- **My Requests**: Your own change requests
- **Recent Activity**: Latest changes and updates
- **Statistics**: Overview of request statuses

## Troubleshooting

### Common Issues and Solutions

#### "Cannot modify partner directly"

**Problem**: You're trying to edit a partner that has an active change request.

**Solution**:

1. Use the change request workflow instead
2. Complete or cancel the existing change request
3. Then make your changes through a new change request

#### "Group Kind is required"

**Problem**: You're creating a group change request without selecting a group kind.

**Solution**:

1. Select a group kind from the dropdown
2. If no group kinds are available, contact your administrator
3. Ensure you have the necessary permissions

#### "Duplicate active requests"

**Problem**: Multiple active change requests exist for the same partner.

**Solution**:

1. Complete or cancel existing requests
2. Create a new request only after previous ones are resolved
3. Contact your administrator if the issue persists

#### "Insufficient permissions"

**Problem**: You don't have permission to perform an action.

**Solution**:

1. Contact your administrator to request permissions
2. Ensure you're assigned to the correct user group
3. Check if your permissions have been updated

### Getting Help

#### Self-Service Options

1. **Check** this user guide
2. **Review** inline help text in the system
3. **Look** at similar requests for examples
4. **Use** the search functionality

#### Contact Support

1. **Report** issues through the system
2. **Contact** your system administrator
3. **Escalate** to technical support if needed
4. **Provide** detailed error messages and steps to reproduce

## Best Practices

### Creating Change Requests

#### Before Creating

1. **Verify** the information is accurate
2. **Check** if a similar request already exists
3. **Ensure** you have all required information
4. **Plan** the changes carefully

#### When Creating

1. **Use** clear, descriptive names
2. **Provide** detailed descriptions
3. **Select** appropriate request type
4. **Include** all relevant information

#### After Creating

1. **Review** the request before submitting
2. **Submit** promptly for approval
3. **Monitor** the approval process
4. **Follow up** if needed

### Managing Group Members

#### Adding Members

1. **Verify** individuals are eligible
2. **Check** for duplicate memberships
3. **Ensure** all required information is complete
4. **Review** the member list before saving

#### Updating Members

1. **Make** changes through the change request workflow
2. **Document** reasons for changes
3. **Notify** affected members if appropriate
4. **Maintain** accurate records

### Approval Process

#### For Approvers

1. **Review** requests promptly
2. **Validate** information thoroughly
3. **Provide** clear feedback
4. **Document** decisions and reasons

#### For Requesters

1. **Respond** to feedback quickly
2. **Make** requested corrections
3. **Resubmit** when ready
4. **Communicate** with approvers as needed

### Data Quality

#### Maintaining Accuracy

1. **Verify** information before submitting
2. **Update** records when information changes
3. **Remove** outdated information
4. **Report** data quality issues

#### Audit Trail

1. **Document** all changes
2. **Provide** clear reasons for changes
3. **Maintain** complete records
4. **Review** audit logs regularly

### Security and Privacy

#### Access Control

1. **Use** appropriate user roles
2. **Follow** security guidelines
3. **Report** security concerns
4. **Maintain** confidentiality

#### Data Protection

1. **Handle** sensitive information carefully
2. **Follow** privacy policies
3. **Secure** access to systems
4. **Report** data breaches immediately

## Advanced Features

### Bulk Operations

#### Multiple Change Requests

1. **Select** multiple requests
2. **Use** bulk actions where available
3. **Review** each request individually
4. **Process** in logical order

#### Group Member Management

1. **Add** multiple members at once
2. **Update** member information in batches
3. **Remove** multiple members if needed
4. **Validate** changes before submitting

### Customization

#### Personal Settings

1. **Configure** notification preferences
2. **Set** default values
3. **Customize** views and filters
4. **Save** frequently used searches

#### Workflow Customization

1. **Request** workflow changes from administrators
2. **Suggest** improvements
3. **Participate** in testing new features
4. **Provide** feedback on usability

### Integration

#### Other Modules

1. **Understand** how change management integrates with other modules
2. **Use** related functionality effectively
3. **Report** integration issues
4. **Suggest** improvements

#### External Systems

1. **Follow** integration guidelines
2. **Maintain** data consistency
3. **Monitor** system performance
4. **Report** issues promptly
