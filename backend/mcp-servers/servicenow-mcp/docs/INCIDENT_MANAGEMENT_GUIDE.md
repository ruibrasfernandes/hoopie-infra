# ServiceNow Incident Management Guide

This guide provides comprehensive information about ServiceNow incident management for AI agents using the ServiceNow MCP server.

## Incident States

ServiceNow incidents follow a standard lifecycle with specific state values:

| State | Value | Description | When to Use |
|-------|-------|-------------|-------------|
| **New** | `1` | Incident just created | Initial state for new incidents |
| **In Progress** | `2` | Work has started | When technician begins working on the incident |
| **On Hold** | `3` | Work temporarily stopped | Waiting for user response, vendor, or other dependencies |
| **Resolved** | `6` | Issue has been fixed | When the root cause is addressed and solution implemented |
| **Closed** | `7` | Incident completed | After user confirms resolution or auto-closure |
| **Canceled** | `8` | Incident invalid/duplicate | When incident is not valid or is a duplicate |

### State Flow Guidelines

**Typical Flow:**
```
New (1) → In Progress (2) → Resolved (6) → Closed (7)
```

**Alternative Flows:**
```
New (1) → Canceled (8)  [Invalid/Duplicate]
In Progress (2) → On Hold (3) → In Progress (2) → Resolved (6)
```

## Priority Matrix

Priority is automatically calculated based on Impact × Urgency:

| Priority | Value | Description | SLA Response Time |
|----------|-------|-------------|-------------------|
| **Critical** | `1` | High Impact + High Urgency | 15 minutes |
| **High** | `2` | High Impact + Medium Urgency OR Medium Impact + High Urgency | 1 hour |
| **Moderate** | `3` | Medium Impact + Medium Urgency OR Low Impact + High Urgency | 8 hours |
| **Low** | `4` | Low Impact + Medium Urgency OR Medium Impact + Low Urgency | 3 days |
| **Planning** | `5` | Low Impact + Low Urgency | 5 days |

## Impact Levels

| Impact | Value | Description | Examples |
|--------|-------|-------------|----------|
| **High** | `1` | Affects multiple users or critical systems | Server down, network outage, critical application failure |
| **Medium** | `2` | Affects single user or non-critical systems | Individual workstation issues, minor application problems |
| **Low** | `3` | Minimal business impact | Enhancement requests, minor inconveniences |

## Urgency Levels

| Urgency | Value | Description | Examples |
|---------|-------|-------------|----------|
| **High** | `1` | Immediate attention required | Production system down, security breach |
| **Medium** | `2` | Attention required soon | Degraded performance, intermittent issues |
| **Low** | `3` | Can wait for normal schedule | Feature requests, non-critical fixes |

## Best Practices for AI Agents

### 1. Incident Creation
- Always set appropriate **Impact** and **Urgency** - Priority will be calculated automatically
- Use clear, descriptive **short_description** (summary)
- Provide detailed **description** with steps to reproduce
- Include **category** and **subcategory** when known
- Set **caller_id** to the affected user

### 2. Incident Updates
- Move to **In Progress (2)** when starting work
- Use **On Hold (3)** when waiting for external dependencies
- Add **work_notes** for internal updates
- Add **comments** for user-facing updates
- Update **assigned_to** when reassigning

### 3. Incident Resolution
- Set state to **Resolved (6)** when fix is implemented
- Always provide **resolution_code** and **resolution_notes**
- Common resolution codes: "Solved (Work Around)", "Solved (Permanently)", "Solved (Not Reproducible)"
- Allow user to verify before closing

### 4. State Management Rules

**Do NOT:**
- Skip states (e.g., New → Resolved)
- Set Closed directly (use Resolved first)
- Use Canceled without proper justification

**Do:**
- Follow the natural flow: New → In Progress → Resolved → Closed
- Use On Hold appropriately with explanations
- Document state changes in work notes

### 5. Common Scenarios

**New Incident Reported:**
```python
create_incident({
    "short_description": "Unable to access email",
    "description": "User reports cannot connect to Outlook since this morning",
    "caller_id": "john.doe",
    "category": "Software",
    "subcategory": "Email",
    "impact": "2",  # Medium - affects one user
    "urgency": "2"  # Medium - not blocking critical work
})
```

**Taking Ownership:**
```python
update_incident({
    "incident_id": "INC0000123",
    "state": "2",  # In Progress
    "assigned_to": "tech.support",
    "work_notes": "Investigating email connectivity issue"
})
```

**Waiting for User Response:**
```python
update_incident({
    "incident_id": "INC0000123",
    "state": "3",  # On Hold
    "work_notes": "Waiting for user to test proposed solution"
})
```

**Resolving Incident:**
```python
resolve_incident({
    "incident_id": "INC0000123",
    "resolution_code": "Solved (Permanently)",
    "resolution_notes": "Reconfigured email client settings. Issue resolved."
})
```

## Query Examples

**Find all open incidents:**
```python
list_incidents({"state": "2"})  # In Progress
```

**Find high priority incidents:**
```python
list_incidents({"priority": "1"})  # Critical
```

**Find incidents by category:**
```python
list_incidents({"category": "Hardware"})
```

**Search incidents by description:**
```python
list_incidents({"description_query": "email"})
```

**Find incidents using ServiceNow query syntax:**
```python
list_incidents({"sysparm_query": "sys_created_on>=2023-01-01 00:00:00^sys_created_on<=2023-02-20 23:59:59"})
list_incidents({"sysparm_query": "priority=1^state!=7"})  # Critical priority, not closed
list_incidents({"sysparm_query": "assigned_to=john.doe^state=2"})  # John's active incidents
```

**Sort and order results:**
```python
# Sort by priority (Critical first)
list_incidents({"order_by": "priority", "order_direction": "asc"})

# Sort by creation date (oldest first)  
list_incidents({"order_by": "sys_created_on", "order_direction": "asc"})

# Sort by incident state
list_incidents({"order_by": "state", "order_direction": "asc"})

# Combine filtering with sorting
list_incidents({
    "state": "2",  # In Progress
    "order_by": "priority", 
    "order_direction": "asc"  # Critical first
})
```

## Integration Guidelines

### For Service Desk Agents
- Use `service_desk` tool package for core incident management
- Focus on New → In Progress → Resolved → Closed flow
- Always document actions in work_notes
- Set appropriate priority based on business impact

### For System Administrators
- Use `full` tool package for comprehensive access
- Monitor Critical/High priority incidents
- Handle escalations and complex technical issues
- Coordinate with other teams as needed

### For Automated Systems
- Create incidents for detected issues
- Update status based on automated remediation
- Use consistent categorization for reporting
- Log all automated actions in work_notes

## Common Pitfalls to Avoid

1. **Incorrect Priority**: Don't manually set priority - use Impact × Urgency
2. **Missing Documentation**: Always add work_notes when changing states
3. **Premature Closure**: Always resolve before closing
4. **Vague Descriptions**: Use specific, actionable descriptions
5. **Ignoring SLAs**: Monitor response times based on priority
6. **Duplicate Incidents**: Search for existing incidents before creating new ones

## Monitoring and Reporting

Key metrics to track:
- **Mean Time to Resolution (MTTR)** by priority
- **First Call Resolution Rate**
- **SLA Compliance** by priority level
- **Incident Volume** by category
- **Reopened Incidents** percentage

Use the incident tools to generate reports and maintain these metrics for continuous improvement.