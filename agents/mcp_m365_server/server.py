"""
MCP Server for Microsoft 365 Resources
Exposes Calendar, Mail, and Tasks via Model Context Protocol
"""

import asyncio
import json
from datetime import datetime
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    ResourceTemplate,
)

from .graph_client import get_graph_client

# Create MCP server
server = Server("m365-context-server")


# ============================================================================
# TOOLS - Callable functions for retrieving M365 data
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_user_profile",
            description="Get the current user's Microsoft 365 profile including name, email, and job title",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_calendar_events",
            description="Get calendar events within a date range. Returns meeting details including subject, time, location, and attendees.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (YYYY-MM-DD). Defaults to today.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD). Defaults to 7 days from start.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return. Default 10.",
                        "default": 10,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_emails",
            description="Get emails from the user's mailbox. Returns subject, sender, date, and preview.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "description": "Mail folder: inbox, sentitems, or drafts. Default inbox.",
                        "enum": ["inbox", "sentitems", "drafts"],
                        "default": "inbox",
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Only return unread emails. Default false.",
                        "default": False,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return. Default 10.",
                        "default": 10,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_tasks",
            description="Get tasks from Microsoft To Do. Returns task title, list, status, importance, and due date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_name": {
                        "type": "string",
                        "description": "Name of specific task list. If omitted, returns tasks from all lists.",
                    },
                    "include_completed": {
                        "type": "boolean",
                        "description": "Include completed tasks. Default false.",
                        "default": False,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of tasks to return. Default 20.",
                        "default": 20,
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute an MCP tool and return results."""
    client = get_graph_client()
    
    try:
        if name == "get_user_profile":
            result = await client.get_user_profile()
            
        elif name == "get_calendar_events":
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            max_results = arguments.get("max_results", 10)
            
            # Convert date strings to ISO format with time
            if start_date:
                start_date = f"{start_date}T00:00:00Z"
            if end_date:
                end_date = f"{end_date}T23:59:59Z"
            
            result = await client.get_calendar_events(start_date, end_date, max_results)
            
        elif name == "get_emails":
            folder = arguments.get("folder", "inbox")
            unread_only = arguments.get("unread_only", False)
            max_results = arguments.get("max_results", 10)
            result = await client.get_emails(folder, unread_only, max_results)
            
        elif name == "get_tasks":
            list_name = arguments.get("list_name")
            include_completed = arguments.get("include_completed", False)
            max_results = arguments.get("max_results", 20)
            result = await client.get_tasks(list_name, include_completed, max_results)
            
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


# ============================================================================
# RESOURCES - Static context about M365 data
# ============================================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available static resources."""
    return [
        Resource(
            uri="m365://user/profile",
            name="User Profile",
            description="Current user's Microsoft 365 profile information",
            mimeType="application/json",
        ),
        Resource(
            uri="m365://calendar/today",
            name="Today's Calendar",
            description="Calendar events for today",
            mimeType="application/json",
        ),
        Resource(
            uri="m365://mail/unread",
            name="Unread Emails",
            description="Unread emails in inbox",
            mimeType="application/json",
        ),
        Resource(
            uri="m365://tasks/pending",
            name="Pending Tasks",
            description="Incomplete tasks from Microsoft To Do",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource and return its content."""
    client = get_graph_client()
    
    try:
        if uri == "m365://user/profile":
            result = await client.get_user_profile()
            
        elif uri == "m365://calendar/today":
            today = datetime.utcnow().strftime("%Y-%m-%d")
            result = await client.get_calendar_events(
                f"{today}T00:00:00Z",
                f"{today}T23:59:59Z",
                20
            )
            
        elif uri == "m365://mail/unread":
            result = await client.get_emails(unread_only=True, max_results=20)
            
        elif uri == "m365://tasks/pending":
            result = await client.get_tasks(include_completed=False, max_results=30)
            
        else:
            return json.dumps({"error": f"Unknown resource: {uri}"})
        
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

async def main():
    """Run the MCP server."""
    print("Starting M365 MCP Server...")
    print("Available tools: get_user_profile, get_calendar_events, get_emails, get_tasks")
    print("Waiting for MCP client connection...\n")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
