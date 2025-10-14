"""
Constants and helper functions for ServiceNow incident management.

This module provides standardized constants and utility functions
for working with ServiceNow incidents.
"""

from enum import Enum
from typing import Dict, Optional


class IncidentState(Enum):
    """ServiceNow incident state values."""
    NEW = "1"
    IN_PROGRESS = "2"
    ON_HOLD = "3"
    RESOLVED = "6"
    CLOSED = "7"
    CANCELED = "8"


class IncidentPriority(Enum):
    """ServiceNow incident priority values."""
    CRITICAL = "1"
    HIGH = "2"
    MODERATE = "3"
    LOW = "4"
    PLANNING = "5"


class IncidentImpact(Enum):
    """ServiceNow incident impact values."""
    HIGH = "1"
    MEDIUM = "2"
    LOW = "3"


class IncidentUrgency(Enum):
    """ServiceNow incident urgency values."""
    HIGH = "1"
    MEDIUM = "2"
    LOW = "3"


# Human-readable mappings
STATE_LABELS = {
    IncidentState.NEW.value: "New",
    IncidentState.IN_PROGRESS.value: "In Progress",
    IncidentState.ON_HOLD.value: "On Hold",
    IncidentState.RESOLVED.value: "Resolved",
    IncidentState.CLOSED.value: "Closed",
    IncidentState.CANCELED.value: "Canceled",
}

PRIORITY_LABELS = {
    IncidentPriority.CRITICAL.value: "Critical",
    IncidentPriority.HIGH.value: "High",
    IncidentPriority.MODERATE.value: "Moderate",
    IncidentPriority.LOW.value: "Low",
    IncidentPriority.PLANNING.value: "Planning",
}

IMPACT_LABELS = {
    IncidentImpact.HIGH.value: "High",
    IncidentImpact.MEDIUM.value: "Medium",
    IncidentImpact.LOW.value: "Low",
}

URGENCY_LABELS = {
    IncidentUrgency.HIGH.value: "High",
    IncidentUrgency.MEDIUM.value: "Medium",
    IncidentUrgency.LOW.value: "Low",
}

# Priority calculation matrix (Impact × Urgency = Priority)
PRIORITY_MATRIX = {
    (IncidentImpact.HIGH.value, IncidentUrgency.HIGH.value): IncidentPriority.CRITICAL.value,
    (IncidentImpact.HIGH.value, IncidentUrgency.MEDIUM.value): IncidentPriority.HIGH.value,
    (IncidentImpact.HIGH.value, IncidentUrgency.LOW.value): IncidentPriority.MODERATE.value,
    (IncidentImpact.MEDIUM.value, IncidentUrgency.HIGH.value): IncidentPriority.HIGH.value,
    (IncidentImpact.MEDIUM.value, IncidentUrgency.MEDIUM.value): IncidentPriority.MODERATE.value,
    (IncidentImpact.MEDIUM.value, IncidentUrgency.LOW.value): IncidentPriority.LOW.value,
    (IncidentImpact.LOW.value, IncidentUrgency.HIGH.value): IncidentPriority.MODERATE.value,
    (IncidentImpact.LOW.value, IncidentUrgency.MEDIUM.value): IncidentPriority.LOW.value,
    (IncidentImpact.LOW.value, IncidentUrgency.LOW.value): IncidentPriority.PLANNING.value,
}

# Common resolution codes
RESOLUTION_CODES = [
    "Solved (Work Around)",
    "Solved (Permanently)",
    "Solved (Not Reproducible)",
    "Solved (Duplicate)",
    "Solved (Cannot Reproduce)",
    "Closed/Resolved by Caller",
    "Not Resolved (Not Reproducible)",
    "Not Resolved (Too Costly)",
]

# SLA response times (in minutes)
SLA_RESPONSE_TIMES = {
    IncidentPriority.CRITICAL.value: 15,
    IncidentPriority.HIGH.value: 60,
    IncidentPriority.MODERATE.value: 480,  # 8 hours
    IncidentPriority.LOW.value: 4320,     # 3 days
    IncidentPriority.PLANNING.value: 7200, # 5 days
}


def get_state_label(state_value: str) -> str:
    """Get human-readable label for incident state."""
    return STATE_LABELS.get(state_value, f"Unknown ({state_value})")


def get_priority_label(priority_value: str) -> str:
    """Get human-readable label for incident priority."""
    return PRIORITY_LABELS.get(priority_value, f"Unknown ({priority_value})")


def get_impact_label(impact_value: str) -> str:
    """Get human-readable label for incident impact."""
    return IMPACT_LABELS.get(impact_value, f"Unknown ({impact_value})")


def get_urgency_label(urgency_value: str) -> str:
    """Get human-readable label for incident urgency."""
    return URGENCY_LABELS.get(urgency_value, f"Unknown ({urgency_value})")


def calculate_priority(impact: str, urgency: str) -> Optional[str]:
    """Calculate priority based on impact and urgency."""
    return PRIORITY_MATRIX.get((impact, urgency))


def get_sla_response_time(priority: str) -> Optional[int]:
    """Get SLA response time in minutes for given priority."""
    return SLA_RESPONSE_TIMES.get(priority)


def is_valid_state_transition(from_state: str, to_state: str) -> bool:
    """Check if state transition is valid."""
    valid_transitions = {
        IncidentState.NEW.value: [IncidentState.IN_PROGRESS.value, IncidentState.CANCELED.value],
        IncidentState.IN_PROGRESS.value: [IncidentState.ON_HOLD.value, IncidentState.RESOLVED.value, IncidentState.CANCELED.value],
        IncidentState.ON_HOLD.value: [IncidentState.IN_PROGRESS.value, IncidentState.RESOLVED.value, IncidentState.CANCELED.value],
        IncidentState.RESOLVED.value: [IncidentState.CLOSED.value, IncidentState.IN_PROGRESS.value],  # Reopening
        IncidentState.CLOSED.value: [IncidentState.IN_PROGRESS.value],  # Reopening
        IncidentState.CANCELED.value: [IncidentState.IN_PROGRESS.value],  # Reopening
    }
    
    return to_state in valid_transitions.get(from_state, [])


def get_incident_summary(incident_data: Dict) -> str:
    """Generate a human-readable summary of an incident."""
    number = incident_data.get("number", "N/A")
    short_desc = incident_data.get("short_description", "N/A")
    state = get_state_label(incident_data.get("state", ""))
    priority = get_priority_label(incident_data.get("priority", ""))
    assigned_to = incident_data.get("assigned_to", "Unassigned")
    
    return f"Incident {number}: {short_desc} | State: {state} | Priority: {priority} | Assigned: {assigned_to}"


def get_next_recommended_states(current_state: str) -> list:
    """Get recommended next states for current state."""
    recommendations = {
        IncidentState.NEW.value: [IncidentState.IN_PROGRESS.value],
        IncidentState.IN_PROGRESS.value: [IncidentState.ON_HOLD.value, IncidentState.RESOLVED.value],
        IncidentState.ON_HOLD.value: [IncidentState.IN_PROGRESS.value],
        IncidentState.RESOLVED.value: [IncidentState.CLOSED.value],
        IncidentState.CLOSED.value: [],
        IncidentState.CANCELED.value: [],
    }
    
    return recommendations.get(current_state, [])


def validate_incident_data(incident_data: Dict) -> list:
    """Validate incident data and return list of issues."""
    issues = []
    
    # Required fields
    if not incident_data.get("short_description"):
        issues.append("Short description is required")
    
    # State validation
    state = incident_data.get("state")
    if state and state not in STATE_LABELS:
        issues.append(f"Invalid state: {state}")
    
    # Priority validation
    priority = incident_data.get("priority")
    if priority and priority not in PRIORITY_LABELS:
        issues.append(f"Invalid priority: {priority}")
    
    # Impact validation
    impact = incident_data.get("impact")
    if impact and impact not in IMPACT_LABELS:
        issues.append(f"Invalid impact: {impact}")
    
    # Urgency validation
    urgency = incident_data.get("urgency")
    if urgency and urgency not in URGENCY_LABELS:
        issues.append(f"Invalid urgency: {urgency}")
    
    # Priority consistency check
    if impact and urgency:
        expected_priority = calculate_priority(impact, urgency)
        if priority and priority != expected_priority:
            issues.append(f"Priority {priority} inconsistent with Impact {impact} × Urgency {urgency} (expected: {expected_priority})")
    
    return issues