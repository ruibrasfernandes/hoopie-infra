# ServiceNow Incident Management Guidelines for AI Agents

## Quick Reference

### Incident States
- **1 = New** - Just created
- **2 = In Progress** - Work started
- **3 = On Hold** - Waiting for dependency
- **6 = Resolved** - Fixed, awaiting closure
- **7 = Closed** - Completed
- **8 = Canceled** - Invalid/duplicate

### Priority Values
- **1 = Critical** - System down, major outage
- **2 = High** - Significant impact
- **3 = Moderate** - Standard issue
- **4 = Low** - Minor issue
- **5 = Planning** - Enhancement/future

### Impact & Urgency
- **1 = High**, **2 = Medium**, **3 = Low**
- Priority is calculated from Impact × Urgency

## Essential Guidelines for AI Agents

### 1. Creating Incidents
```python
# Always include these fields
create_incident({
    "short_description": "Clear, concise summary",
    "description": "Detailed description with steps to reproduce",
    "caller_id": "affected.user",
    "impact": "2",  # 1=High, 2=Medium, 3=Low
    "urgency": "2", # 1=High, 2=Medium, 3=Low
    "category": "Software",
    "subcategory": "Email"
})
```

### 2. State Management Rules
- **ALWAYS** follow the flow: New → In Progress → Resolved → Closed
- **NEVER** skip states (e.g., New → Resolved)
- **USE** "In Progress" when starting work
- **USE** "On Hold" when waiting for external dependencies
- **USE** "Resolved" when fix is implemented
- **USE** "Closed" only after user confirms resolution

### 3. Priority Decision Matrix

| Impact | Urgency | Priority | Response Time |
|--------|---------|----------|---------------|
| High | High | Critical (1) | 15 minutes |
| High | Medium | High (2) | 1 hour |
| Medium | High | High (2) | 1 hour |
| Medium | Medium | Moderate (3) | 8 hours |
| Low | High | Moderate (3) | 8 hours |
| Low | Medium | Low (4) | 3 days |
| Low | Low | Planning (5) | 5 days |

### 4. When to Use Each State

**New (1):**
- Initial state for all new incidents
- User has reported an issue
- No work has started yet

**In Progress (2):**
- Technician has started working
- Investigation is underway
- Actively troubleshooting

**On Hold (3):**
- Waiting for user response
- Waiting for vendor
- Waiting for parts/equipment
- Escalated to another team

**Resolved (6):**
- Root cause identified and fixed
- Solution has been implemented
- Ready for user verification
- Include resolution code and notes

**Closed (7):**
- User has confirmed resolution
- No further action needed
- Auto-closed after time period

**Canceled (8):**
- Duplicate incident
- Invalid request
- User withdrew request

### 5. Documentation Requirements

**Work Notes (Internal):**
- Add when changing states
- Document troubleshooting steps
- Record findings and actions
- Include time spent

**Comments (User-facing):**
- Communicate with end users
- Provide status updates
- Request additional information
- Confirm resolution

### 6. Common Scenarios

**Email Issues:**
```python
create_incident({
    "short_description": "Unable to send emails",
    "description": "User reports Outlook freezes when sending emails",
    "impact": "2",  # Medium - affects productivity
    "urgency": "2", # Medium - not blocking critical work
    "category": "Software",
    "subcategory": "Email"
})
```

**Server Down:**
```python
create_incident({
    "short_description": "Production server unavailable",
    "description": "Web application server not responding",
    "impact": "1",  # High - affects many users
    "urgency": "1", # High - immediate attention needed
    "category": "Hardware",
    "subcategory": "Server"
})
```

**Password Reset:**
```python
create_incident({
    "short_description": "Password reset request",
    "description": "User locked out of system",
    "impact": "2",  # Medium - affects one user
    "urgency": "2", # Medium - user can't work
    "category": "Security",
    "subcategory": "Access"
})
```

### 7. Updating Incidents

**Starting Work:**
```python
update_incident({
    "incident_id": "INC0000123",
    "state": "2",  # In Progress
    "assigned_to": "tech.support",
    "work_notes": "Beginning investigation of email issue"
})
```

**Waiting for User:**
```python
update_incident({
    "incident_id": "INC0000123",
    "state": "3",  # On Hold
    "work_notes": "Emailed user for additional details",
    "comments": "Please provide error message screenshot"
})
```

**Resolving:**
```python
resolve_incident({
    "incident_id": "INC0000123",
    "resolution_code": "Solved (Permanently)",
    "resolution_notes": "Reconfigured email client settings"
})
```

### 8. Search and Filtering

**Find urgent incidents:**
```python
list_incidents({"priority": "1"})  # Critical priority
list_incidents({"priority": "2"})  # High priority
```

**Find open work:**
```python
list_incidents({"state": "2"})  # In Progress
list_incidents({"assigned_to": "john.doe"})  # Specific user
```

**Find by category:**
```python
list_incidents({"category": "Hardware"})
list_incidents({"description_query": "email"})  # Search description
```

**Ordering and Pagination:**
```python
# Get latest incidents (default behavior - newest first)
list_incidents({"limit": 20})

# Get oldest incidents first (by creation date)
list_incidents({"order_direction": "asc"})

# Order by priority (1=Critical first, then 2=High, etc.)
list_incidents({"order_by": "priority", "order_direction": "asc"})

# Order by priority (5=Planning first, then 4=Low, etc.)
list_incidents({"order_by": "priority", "order_direction": "desc"})

# Order by state (1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed)
list_incidents({"order_by": "state", "order_direction": "asc"})

# Order by incident number (newest incident numbers first)
list_incidents({"order_by": "number", "order_direction": "desc"})

# Order by updated date (most recently updated first)
list_incidents({"order_by": "sys_updated_on", "order_direction": "desc"})

# Pagination - get next 10 incidents
list_incidents({"limit": 10, "offset": 10})
```

**Available Sort Fields:**
- `sys_created_on` (default) - Creation timestamp
- `sys_updated_on` - Last updated timestamp  
- `priority` - Priority level (1-5)
- `state` - Incident state
- `number` - Incident number
- `urgency` - Urgency level
- `impact` - Impact level
- `short_description` - Incident title
- `assigned_to` - Assigned user
- `opened_at` - When incident was opened

**Response Information:**
```python
# The response includes count and total information:
{
  "success": true,
  "count": 10,           # Number of incidents returned in this page
  "total_count": 150,    # Total incidents matching the query (for pagination)
  "message": "Returning 10, Found 150 Incidents",
  "incidents": [...]
}
```

**Advanced queries using ServiceNow syntax:**
```python
list_incidents({"sysparm_query": "sys_created_on>=2023-01-01^priority<=2"})  # Recent high priority
list_incidents({"sysparm_query": "assigned_to=john.doe^state=2"})  # John's active work
list_incidents({"sysparm_query": "sys_created_on>=javascript:gs.daysAgo(7)^state!=7"})  # Last 7 days, not closed
```

### 9. Error Prevention

**DON'T:**
- Set priority manually (use impact × urgency)
- Skip state transitions
- Close without resolving first
- Use vague descriptions
- Forget to document actions

**DO:**
- Use specific, actionable descriptions
- Follow proper state flow
- Document all state changes
- Set appropriate impact/urgency
- Include resolution details

### 10. Escalation Guidelines

**Escalate when:**
- Critical incidents (Priority 1)
- SLA about to be breached
- Complex technical issues
- User complaints about service
- Incidents requiring specialized skills

**Escalation Process:**
1. Update work notes with current status
2. Assign to appropriate escalation group
3. Set state to "In Progress"
4. Add detailed handoff notes
5. Notify receiving team

### 11. Quality Checklist

Before updating any incident, verify:
- [ ] Appropriate state transition
- [ ] Clear work notes added
- [ ] Correct priority based on impact/urgency
- [ ] User communication if needed
- [ ] Assignment to correct technician
- [ ] Category and subcategory set
- [ ] Resolution details complete (if resolving)

### 12. Performance Metrics

Monitor these KPIs:
- **First Call Resolution**: Resolve on first contact
- **Mean Time to Resolution**: Average time to resolve
- **SLA Compliance**: Meet response time targets
- **Customer Satisfaction**: User rating of service
- **Reopen Rate**: Incidents reopened after closure

Use these metrics to improve incident handling and identify training needs.

---

## Technical Implementation Notes

### ServiceNow API Sorting Implementation

The `list_incidents` tool uses ServiceNow's Table API with proper sorting syntax:

**Implementation Details:**
- Sorting is implemented using `ORDERBY` and `ORDERBYDESC` operators within the `sysparm_query` parameter
- Parameters `order_by` and `order_direction` are converted to ServiceNow's native sorting format:
  - `order_direction="asc"` → `ORDERBY{field_name}`
  - `order_direction="desc"` → `ORDERBYDESC{field_name}`
- Sorting filters are combined with other query filters using the `^` (AND) operator

**Example API Calls:**
```
GET /api/now/table/incident?sysparm_query=state=2^ORDERBYpriority&sysparm_limit=10
GET /api/now/table/incident?sysparm_query=ORDERBYDESCsys_created_on&sysparm_limit=10
```

This ensures proper sorting functionality that complies with ServiceNow's Table API specifications.