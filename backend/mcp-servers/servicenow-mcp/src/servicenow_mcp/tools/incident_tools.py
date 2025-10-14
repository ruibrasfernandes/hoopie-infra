"""
Incident tools for the ServiceNow MCP server.

This module provides tools for managing incidents in ServiceNow.
"""

import logging
from typing import Optional, List, Literal

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class CreateIncidentParams(BaseModel):
    """Parameters for creating an incident."""

    short_description: str = Field(..., description="Short description of the incident")
    description: Optional[str] = Field(None, description="Detailed description of the incident")
    caller_id: Optional[str] = Field(None, description="User who reported the incident")
    category: Optional[str] = Field(None, description="Category of the incident")
    subcategory: Optional[str] = Field(None, description="Subcategory of the incident")
    priority: Optional[Literal["1", "2", "3", "4", "5"]] = Field(None, description="Priority of the incident. Values: 1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning")
    impact: Optional[Literal["1", "2", "3"]] = Field(None, description="Impact of the incident. Values: 1=High, 2=Medium, 3=Low")
    urgency: Optional[Literal["1", "2", "3"]] = Field(None, description="Urgency of the incident. Values: 1=High, 2=Medium, 3=Low")
    assigned_to: Optional[str] = Field(None, description="User assigned to the incident")
    assignment_group: Optional[str] = Field(None, description="Group assigned to the incident")


class UpdateIncidentParams(BaseModel):
    """Parameters for updating an incident."""

    incident_id: str = Field(..., description="Incident ID or sys_id")
    short_description: Optional[str] = Field(None, description="Short description of the incident")
    description: Optional[str] = Field(None, description="Detailed description of the incident")
    state: Optional[Literal["1", "2", "3", "6", "7", "8"]] = Field(None, description="State of the incident. Values: 1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed, 8=Canceled")
    category: Optional[str] = Field(None, description="Category of the incident")
    subcategory: Optional[str] = Field(None, description="Subcategory of the incident")
    priority: Optional[Literal["1", "2", "3", "4", "5"]] = Field(None, description="Priority of the incident. Values: 1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning")
    impact: Optional[Literal["1", "2", "3"]] = Field(None, description="Impact of the incident. Values: 1=High, 2=Medium, 3=Low")
    urgency: Optional[Literal["1", "2", "3"]] = Field(None, description="Urgency of the incident. Values: 1=High, 2=Medium, 3=Low")
    assigned_to: Optional[str] = Field(None, description="User assigned to the incident")
    assignment_group: Optional[str] = Field(None, description="Group assigned to the incident")
    work_notes: Optional[str] = Field(None, description="Work notes to add to the incident")
    close_notes: Optional[str] = Field(None, description="Close notes to add to the incident")
    close_code: Optional[str] = Field(None, description="Close code for the incident")


class AddCommentParams(BaseModel):
    """Parameters for adding a comment to an incident."""

    incident_id: str = Field(..., description="Incident ID or sys_id")
    comment: str = Field(..., description="Comment to add to the incident")
    is_work_note: bool = Field(False, description="Whether the comment is a work note")


class ResolveIncidentParams(BaseModel):
    """Parameters for resolving an incident."""

    incident_id: str = Field(..., description="Incident ID or sys_id")
    resolution_code: str = Field(..., description="Resolution code for the incident")
    resolution_notes: str = Field(..., description="Resolution notes for the incident")


class GetIncidentParams(BaseModel):
    """Parameters for getting a specific incident."""
    
    incident_id: str = Field(..., description="Incident ID (number like INC0000123) or sys_id")


class ListIncidentsParams(BaseModel):
    """Parameters for listing incidents."""
    
    limit: int = Field(10, description="Maximum number of incidents to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[Literal["1", "2", "3", "6", "7", "8"]] = Field(None, description="Filter by incident state. Values: 1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed, 8=Canceled")
    assigned_to: Optional[str] = Field(None, description="Filter by assigned user")
    category: Optional[str] = Field(None, description="Filter by category")
    description_query: Optional[str] = Field(None, description="Text search query for incident descriptions (searches short_description and description fields)")
    sysparm_query: str = Field("", description="Additional ServiceNow query filter")
    order_by: Literal["sys_created_on", "sys_updated_on", "priority", "state", "number", "urgency", "impact", "short_description", "assigned_to", "opened_at"] = Field("sys_created_on", description="Field to order results by (default: sys_created_on)")
    order_direction: Literal["asc", "desc"] = Field("desc", description="Order direction: 'asc' for ascending, 'desc' for descending (default: desc)")


class IncidentResponse(BaseModel):
    """Response from incident operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    incident_id: Optional[str] = Field(None, description="ID of the affected incident")
    incident_number: Optional[str] = Field(None, description="Number of the affected incident")


def create_incident(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateIncidentParams,
) -> IncidentResponse:
    """
    Create a new incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for creating the incident.

    Returns:
        Response with the created incident details.
    """
    api_url = f"{config.api_url}/table/incident"

    # Build request data
    data = {
        "short_description": params.short_description,
    }

    if params.description:
        data["description"] = params.description
    if params.caller_id:
        data["caller_id"] = params.caller_id
    if params.category:
        data["category"] = params.category
    if params.subcategory:
        data["subcategory"] = params.subcategory
    if params.priority:
        data["priority"] = params.priority
    if params.impact:
        data["impact"] = params.impact
    if params.urgency:
        data["urgency"] = params.urgency
    if params.assigned_to:
        data["assigned_to"] = params.assigned_to
    if params.assignment_group:
        data["assignment_group"] = params.assignment_group

    # Make request
    try:
        response = requests.post(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return IncidentResponse(
            success=True,
            message="Incident created successfully",
            incident_id=result.get("sys_id"),
            incident_number=result.get("number"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create incident: {e}")
        return IncidentResponse(
            success=False,
            message=f"Failed to create incident: {str(e)}",
        )


def update_incident(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateIncidentParams,
) -> IncidentResponse:
    """
    Update an existing incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for updating the incident.

    Returns:
        Response with the updated incident details.
    """
    # Determine if incident_id is a number or sys_id
    incident_id = params.incident_id
    if len(incident_id) == 32 and all(c in "0123456789abcdef" for c in incident_id):
        # This is likely a sys_id
        api_url = f"{config.api_url}/table/incident/{incident_id}"
    else:
        # This is likely an incident number
        # First, we need to get the sys_id
        try:
            query_url = f"{config.api_url}/table/incident"
            query_params = {
                "sysparm_query": f"number={incident_id}",
                "sysparm_limit": 1,
            }

            response = requests.get(
                query_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if not result:
                return IncidentResponse(
                    success=False,
                    message=f"Incident not found: {incident_id}",
                )

            incident_id = result[0].get("sys_id")
            api_url = f"{config.api_url}/table/incident/{incident_id}"

        except requests.RequestException as e:
            logger.error(f"Failed to find incident: {e}")
            return IncidentResponse(
                success=False,
                message=f"Failed to find incident: {str(e)}",
            )

    # Build request data
    data = {}

    if params.short_description:
        data["short_description"] = params.short_description
    if params.description:
        data["description"] = params.description
    if params.state:
        data["state"] = params.state
    if params.category:
        data["category"] = params.category
    if params.subcategory:
        data["subcategory"] = params.subcategory
    if params.priority:
        data["priority"] = params.priority
    if params.impact:
        data["impact"] = params.impact
    if params.urgency:
        data["urgency"] = params.urgency
    if params.assigned_to:
        data["assigned_to"] = params.assigned_to
    if params.assignment_group:
        data["assignment_group"] = params.assignment_group
    if params.work_notes:
        data["work_notes"] = params.work_notes
    if params.close_notes:
        data["close_notes"] = params.close_notes
    if params.close_code:
        data["close_code"] = params.close_code

    # Make request
    try:
        response = requests.put(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return IncidentResponse(
            success=True,
            message="Incident updated successfully",
            incident_id=result.get("sys_id"),
            incident_number=result.get("number"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to update incident: {e}")
        return IncidentResponse(
            success=False,
            message=f"Failed to update incident: {str(e)}",
        )


def add_comment(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: AddCommentParams,
) -> IncidentResponse:
    """
    Add a comment to an incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for adding the comment.

    Returns:
        Response with the result of the operation.
    """
    # Determine if incident_id is a number or sys_id
    incident_id = params.incident_id
    if len(incident_id) == 32 and all(c in "0123456789abcdef" for c in incident_id):
        # This is likely a sys_id
        api_url = f"{config.api_url}/table/incident/{incident_id}"
    else:
        # This is likely an incident number
        # First, we need to get the sys_id
        try:
            query_url = f"{config.api_url}/table/incident"
            query_params = {
                "sysparm_query": f"number={incident_id}",
                "sysparm_limit": 1,
            }

            response = requests.get(
                query_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if not result:
                return IncidentResponse(
                    success=False,
                    message=f"Incident not found: {incident_id}",
                )

            incident_id = result[0].get("sys_id")
            api_url = f"{config.api_url}/table/incident/{incident_id}"

        except requests.RequestException as e:
            logger.error(f"Failed to find incident: {e}")
            return IncidentResponse(
                success=False,
                message=f"Failed to find incident: {str(e)}",
            )

    # Build request data
    data = {}

    if params.is_work_note:
        data["work_notes"] = params.comment
    else:
        data["comments"] = params.comment

    # Make request
    try:
        response = requests.put(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return IncidentResponse(
            success=True,
            message="Comment added successfully",
            incident_id=result.get("sys_id"),
            incident_number=result.get("number"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to add comment: {e}")
        return IncidentResponse(
            success=False,
            message=f"Failed to add comment: {str(e)}",
        )


def resolve_incident(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ResolveIncidentParams,
) -> IncidentResponse:
    """
    Resolve an incident in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for resolving the incident.

    Returns:
        Response with the result of the operation.
    """
    # Determine if incident_id is a number or sys_id
    incident_id = params.incident_id
    if len(incident_id) == 32 and all(c in "0123456789abcdef" for c in incident_id):
        # This is likely a sys_id
        api_url = f"{config.api_url}/table/incident/{incident_id}"
    else:
        # This is likely an incident number
        # First, we need to get the sys_id
        try:
            query_url = f"{config.api_url}/table/incident"
            query_params = {
                "sysparm_query": f"number={incident_id}",
                "sysparm_limit": 1,
            }

            response = requests.get(
                query_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if not result:
                return IncidentResponse(
                    success=False,
                    message=f"Incident not found: {incident_id}",
                )

            incident_id = result[0].get("sys_id")
            api_url = f"{config.api_url}/table/incident/{incident_id}"

        except requests.RequestException as e:
            logger.error(f"Failed to find incident: {e}")
            return IncidentResponse(
                success=False,
                message=f"Failed to find incident: {str(e)}",
            )

    # Build request data
    data = {
        "state": "6",  # Resolved
        "close_code": params.resolution_code,
        "close_notes": params.resolution_notes,
        "resolved_at": "now",
    }

    # Make request
    try:
        response = requests.put(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return IncidentResponse(
            success=True,
            message="Incident resolved successfully",
            incident_id=result.get("sys_id"),
            incident_number=result.get("number"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to resolve incident: {e}")
        return IncidentResponse(
            success=False,
            message=f"Failed to resolve incident: {str(e)}",
        )


def get_incident(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetIncidentParams,
) -> dict:
    """
    Get a specific incident from ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting the incident.

    Returns:
        Dictionary with the incident details.
    """
    logger.info(f"get_incident called with incident_id: {params.incident_id}")
    
    # Determine if incident_id is a number or sys_id
    incident_id = params.incident_id
    if len(incident_id) == 32 and all(c in "0123456789abcdef" for c in incident_id):
        # This is likely a sys_id - direct access
        try:
            api_url = f"{config.api_url}/table/incident/{incident_id}"
            response = requests.get(
                api_url,
                params={
                    "sysparm_display_value": "true",
                    "sysparm_exclude_reference_link": "true",
                },
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", {})
            if not result:
                return {
                    "success": False,
                    "message": f"Incident not found: {incident_id}",
                    "incident": None
                }

            incident_data = result
            
        except requests.RequestException as e:
            logger.error(f"Failed to get incident: {e}")
            return {
                "success": False,
                "message": f"Failed to get incident: {str(e)}",
                "incident": None
            }
    else:
        # This is likely an incident number - search for it
        try:
            query_url = f"{config.api_url}/table/incident"
            query_params = {
                "sysparm_query": f"number={incident_id}",
                "sysparm_limit": 1,
                "sysparm_display_value": "true",
                "sysparm_exclude_reference_link": "true",
            }

            response = requests.get(
                query_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if not result:
                return {
                    "success": False,
                    "message": f"Incident not found: {incident_id}",
                    "incident": None
                }

            incident_data = result[0]
            
        except requests.RequestException as e:
            logger.error(f"Failed to find incident: {e}")
            return {
                "success": False,
                "message": f"Failed to find incident: {str(e)}",
                "incident": None
            }

    # Process the incident data
    try:
        # Handle assigned_to field which could be a string or a dictionary
        assigned_to = incident_data.get("assigned_to")
        if isinstance(assigned_to, dict):
            assigned_to = assigned_to.get("display_value")
        
        # Handle caller_id field
        caller_id = incident_data.get("caller_id")
        if isinstance(caller_id, dict):
            caller_id = caller_id.get("display_value")
        
        # Handle assignment_group field
        assignment_group = incident_data.get("assignment_group")
        if isinstance(assignment_group, dict):
            assignment_group = assignment_group.get("display_value")

        incident = {
            "sys_id": incident_data.get("sys_id"),
            "number": incident_data.get("number"),
            "short_description": incident_data.get("short_description"),
            "description": incident_data.get("description"),
            "state": incident_data.get("state"),
            "priority": incident_data.get("priority"),
            "impact": incident_data.get("impact"),
            "urgency": incident_data.get("urgency"),
            "assigned_to": assigned_to,
            "assignment_group": assignment_group,
            "caller_id": caller_id,
            "category": incident_data.get("category"),
            "subcategory": incident_data.get("subcategory"),
            "created_on": incident_data.get("sys_created_on"),
            "updated_on": incident_data.get("sys_updated_on"),
            "opened_at": incident_data.get("opened_at"),
            "resolved_at": incident_data.get("resolved_at"),
            "closed_at": incident_data.get("closed_at"),
            "work_notes": incident_data.get("work_notes"),
            "comments": incident_data.get("comments"),
            "close_code": incident_data.get("close_code"),
            "close_notes": incident_data.get("close_notes"),
            "sla_due": incident_data.get("sla_due"),
        }
        
        return {
            "success": True,
            "message": "Incident retrieved successfully",
            "incident": incident
        }
        
    except Exception as e:
        logger.error(f"Error processing incident data: {e}")
        return {
            "success": False,
            "message": f"Error processing incident data: {str(e)}",
            "incident": None
        }


def list_incidents(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListIncidentsParams,
) -> dict:
    """
    List incidents from ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing incidents.

    Returns:
        Dictionary with list of incidents.
    """
    logger.info(f"list_incidents called with config.instance_url: {config.instance_url}")
    logger.info(f"API URL: {config.api_url}")
    logger.info(f"Received parameters: {params}")
    logger.info(f"Received parameters type: {type(params)}")
    logger.info(f"sysparm_query value: '{params.sysparm_query}'")
    logger.info(f"order_by param: '{params.order_by}' (type: {type(params.order_by)})")
    logger.info(f"order_direction param: '{params.order_direction}' (type: {type(params.order_direction)})")
    logger.info(f"order_by is None: {params.order_by is None}")
    logger.info(f"order_direction is None: {params.order_direction is None}")
    
    api_url = f"{config.api_url}/table/incident"

    # Build query parameters 
    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }
    
    # Build query filters
    filters = []
    
    # Add individual field filters
    if params.state:
        filters.append(f"state={params.state}")
    if params.assigned_to:
        filters.append(f"assigned_to={params.assigned_to}")
    if params.category:
        filters.append(f"category={params.category}")
    if params.description_query:
        filters.append(f"short_descriptionLIKE{params.description_query}^ORdescriptionLIKE{params.description_query}")
    
    # Add sysparm_query if provided
    if params.sysparm_query and params.sysparm_query.strip():
        filters.append(params.sysparm_query.strip())
        logger.info(f"Added sysparm_query filter: {params.sysparm_query.strip()}")
    
    # Add sorting to filters using ServiceNow API format
    order_by = params.order_by if params.order_by else "sys_created_on"
    order_direction = params.order_direction if params.order_direction else "desc"
    
    logger.info(f"Using order_by: '{order_by}', order_direction: '{order_direction}'")
    
    # Add sorting using ServiceNow's ORDERBY syntax
    if order_direction.lower() == "desc":
        sort_filter = f"ORDERBYDESC{order_by}"
    else:
        sort_filter = f"ORDERBY{order_by}"
    
    filters.append(sort_filter)
    logger.info(f"Added sorting filter: {sort_filter}")
    
    # Combine all filters with AND logic
    logger.info(f"All filters before combination: {filters}")
    if filters:
        query_params["sysparm_query"] = "^".join(filters)
        logger.info(f"Built filters: {filters}")
        logger.info(f"Final sysparm_query: {query_params.get('sysparm_query')}")
    else:
        logger.info("No filters were built")
    
    # Make request
    try:
        headers = auth_manager.get_headers()
        logger.info(f"Making request to: {api_url}")
        logger.info(f"Query params: {query_params}")
        logger.info(f"Headers: {dict(headers)}")  # Log headers (auth will be visible in debug logs)
        
        response = requests.get(
            api_url,
            params=query_params,
            headers=headers,
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        data = response.json()
        incidents = []
        
        for incident_data in data.get("result", []):
            # Handle assigned_to field which could be a string or a dictionary
            assigned_to = incident_data.get("assigned_to")
            if isinstance(assigned_to, dict):
                assigned_to = assigned_to.get("display_value")
            
            incident = {
                "sys_id": incident_data.get("sys_id"),
                "number": incident_data.get("number"),
                "short_description": incident_data.get("short_description"),
                "description": incident_data.get("description"),
                "state": incident_data.get("state"),
                "priority": incident_data.get("priority"),
                "assigned_to": assigned_to,
                "category": incident_data.get("category"),
                "subcategory": incident_data.get("subcategory"),
                "created_on": incident_data.get("sys_created_on"),
                "updated_on": incident_data.get("sys_updated_on"),
                "sla_due": incident_data.get("sla_due"),
            }
            incidents.append(incident)
        
        # Try to get total count from response headers or data
        total_count = None
        if 'X-Total-Count' in response.headers:
            total_count = int(response.headers['X-Total-Count'])
        elif 'total' in data:
            total_count = int(data['total'])
        
        count = len(incidents)
        
        # Build message with count and total_count
        if total_count is not None:
            message = f"Returning {count}, Found {total_count} Incidents"
        else:
            message = f"Returning {count} Incidents"
        
        result = {
            "success": True,
            "count": count,
        }
        
        if total_count is not None:
            result["total_count"] = total_count
        
        result.update({
            "message": message,
            "incidents": incidents,
        })
        
        return result
        
    except requests.RequestException as e:
        logger.error(f"Failed to list incidents: {e}")
        return {
            "success": False,
            "message": f"Failed to list incidents: {str(e)}",
            "incidents": []
        }
