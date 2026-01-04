"""
Personal Assistant Agent - Main Orchestrator
Combines M365 MCP Server (Agent A) with Scheduler Tools (Agent B)
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Optional

# Add parent paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter

from agents.scheduler_agent.agent import get_scheduler


class PersonalAssistant:
    """
    Personal Productivity Assistant that orchestrates:
    - Agent A (MCP Server): Microsoft 365 data access
    - Agent B (Scheduler): Scheduling and prioritization tools
    """
    
    def __init__(self):
        self.mcp_session: Optional[ClientSession] = None
        self.scheduler = get_scheduler()
        self._mcp_process = None
    
    async def connect_to_mcp(self):
        """Connect to the M365 MCP server."""
        if self.mcp_session is not None:
            return
        
        # Path to MCP server
        server_script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "mcp_m365_server",
            "server.py"
        )
        
        python_path = sys.executable
        
        server_params = StdioServerParameters(
            command=python_path,
            args=["-m", "agents.mcp_m365_server.server"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )
        
        # This will be called when we need MCP access
        print("MCP Server connection configured (will connect on first use)")
    
    async def _call_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the MCP server."""
        # For now, we'll call the Graph client directly since we're in the same process
        # In a full implementation, this would use the MCP client
        from agents.mcp_m365_server.graph_client import get_graph_client
        
        client = get_graph_client()
        
        if tool_name == "get_user_profile":
            return await client.get_user_profile()
        elif tool_name == "get_calendar_events":
            start = arguments.get("start_date")
            end = arguments.get("end_date")
            if start:
                start = f"{start}T00:00:00Z"
            if end:
                end = f"{end}T23:59:59Z"
            return await client.get_calendar_events(start, end, arguments.get("max_results", 10))
        elif tool_name == "get_emails":
            return await client.get_emails(
                arguments.get("folder", "inbox"),
                arguments.get("unread_only", False),
                arguments.get("max_results", 10)
            )
        elif tool_name == "get_tasks":
            return await client.get_tasks(
                arguments.get("list_name"),
                arguments.get("include_completed", False),
                arguments.get("max_results", 20)
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def get_daily_briefing(self) -> str:
        """Get a daily briefing with calendar, emails, and tasks."""
        try:
            # Get data from MCP server (Agent A)
            profile = await self._call_mcp_tool("get_user_profile", {})
            events = await self._call_mcp_tool("get_calendar_events", {"max_results": 10})
            emails = await self._call_mcp_tool("get_emails", {"unread_only": True, "max_results": 10})
            tasks = await self._call_mcp_tool("get_tasks", {"max_results": 10})
            
            # Process with Scheduler agent (Agent B)
            email_summary = self.scheduler.summarize_emails(emails)
            prioritized_tasks = self.scheduler.prioritize_tasks(tasks)
            
            # Build briefing
            name = profile.get("displayName", "there")
            briefing = f"# Good morning, {name}! 👋\n\n"
            
            # Calendar section
            briefing += "## 📅 Today's Schedule\n"
            if events:
                for event in events[:5]:
                    time = event.get("start", "")[:16].replace("T", " ")
                    briefing += f"- **{event.get('subject')}** at {time}\n"
            else:
                briefing += "- No meetings scheduled today\n"
            briefing += "\n"
            
            # Email section
            briefing += "## 📧 Email Summary\n"
            briefing += f"{email_summary.get('summary', 'No new emails')}\n"
            if email_summary.get("categories", {}).get("action_required", {}).get("count", 0) > 0:
                briefing += "\n**Emails needing action:**\n"
                for email in email_summary["categories"]["action_required"]["emails"][:3]:
                    briefing += f"- {email.get('subject')} (from {email.get('from')})\n"
            briefing += "\n"
            
            # Tasks section
            briefing += "## ✅ Priority Tasks\n"
            if prioritized_tasks:
                for task in prioritized_tasks[:5]:
                    rec = task.get("recommendation", "")
                    briefing += f"- {rec} **{task.get('title')}**\n"
            else:
                briefing += "- No pending tasks\n"
            
            return briefing
            
        except Exception as e:
            return f"I couldn't fetch your briefing right now. Error: {str(e)}\n\nMake sure you're authenticated with Microsoft 365."
    
    async def find_meeting_time(self, duration: int = 30, days: int = 5) -> str:
        """Find available time slots for a meeting."""
        try:
            from datetime import datetime, timedelta
            
            start = datetime.now().strftime("%Y-%m-%d")
            end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Get calendar from MCP (Agent A)
            events = await self._call_mcp_tool("get_calendar_events", {
                "start_date": start,
                "end_date": end,
                "max_results": 50
            })
            
            # Find slots with Scheduler (Agent B)
            slots = self.scheduler.find_available_slots(
                events,
                duration_minutes=duration,
                start_date=start,
                end_date=end
            )
            
            if not slots:
                return "I couldn't find any available slots in the next {days} days."
            
            response = f"## Available {duration}-minute slots:\n\n"
            for slot in slots[:5]:
                day = slot.get("day", "")
                start_time = slot.get("start", "")[-8:-3]
                end_time = slot.get("end", "")[-8:-3]
                response += f"- **{day}**: {start_time} - {end_time}\n"
            
            return response
            
        except Exception as e:
            return f"Error finding meeting times: {str(e)}"
    
    async def get_task_priorities(self) -> str:
        """Get prioritized task list."""
        try:
            # Get tasks from MCP (Agent A)
            tasks = await self._call_mcp_tool("get_tasks", {"max_results": 20})
            
            # Prioritize with Scheduler (Agent B)
            prioritized = self.scheduler.prioritize_tasks(tasks, criteria="balanced")
            
            if not prioritized:
                return "You have no pending tasks! 🎉"
            
            response = "## Your Prioritized Tasks\n\n"
            for i, task in enumerate(prioritized[:10], 1):
                rec = task.get("recommendation", "")
                title = task.get("title", "Untitled")
                reasons = ", ".join(task.get("priority_reasons", []))
                
                response += f"{i}. {rec} **{title}**"
                if reasons:
                    response += f" ({reasons})"
                response += "\n"
            
            return response
            
        except Exception as e:
            return f"Error getting tasks: {str(e)}"
    
    async def summarize_inbox(self) -> str:
        """Get email inbox summary."""
        try:
            # Get emails from MCP (Agent A)
            emails = await self._call_mcp_tool("get_emails", {"max_results": 20})
            
            # Summarize with Scheduler (Agent B)
            summary = self.scheduler.summarize_emails(emails)
            
            response = "## 📧 Inbox Summary\n\n"
            response += f"**Total:** {summary.get('total_count', 0)} emails\n"
            response += f"**Unread:** {summary.get('unread_count', 0)}\n"
            response += f"**Important:** {summary.get('important_count', 0)}\n\n"
            
            categories = summary.get("categories", {})
            
            if categories.get("action_required", {}).get("count", 0) > 0:
                response += "### 📌 Action Required\n"
                for email in categories["action_required"]["emails"]:
                    response += f"- **{email.get('subject')}** from {email.get('from')}\n"
                response += "\n"
            
            if categories.get("meetings", {}).get("count", 0) > 0:
                response += "### 📅 Meeting Related\n"
                for email in categories["meetings"]["emails"]:
                    response += f"- **{email.get('subject')}** from {email.get('from')}\n"
                response += "\n"
            
            return response
            
        except Exception as e:
            return f"Error summarizing inbox: {str(e)}"


# Create the agent application
assistant = PersonalAssistant()

AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(),
    adapter=CloudAdapter()
)


# ============================================================================
# CONVERSATION HANDLERS
# ============================================================================

async def _welcome(context: TurnContext, _: TurnState):
    """Welcome message for new users."""
    await context.send_activity(
        "👋 **Welcome to your Personal Productivity Hub!**\n\n"
        "I'm your AI assistant that helps you manage your:\n"
        "- 📅 Calendar & meetings\n"
        "- 📧 Emails\n"
        "- ✅ Tasks\n\n"
        "**Try these commands:**\n"
        "- `briefing` - Get your daily overview\n"
        "- `schedule` - Find meeting times\n"
        "- `tasks` - View prioritized tasks\n"
        "- `inbox` - Summarize your emails\n"
        "- `help` - Show all commands\n\n"
        "Let's get started! Type `briefing` for your daily overview."
    )

AGENT_APP.conversation_update("membersAdded")(_welcome)


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _: TurnState):
    """Handle incoming messages."""
    text = (context.activity.text or "").strip().lower()
    
    if text in ["help", "/help", "?"]:
        await context.send_activity(
            "## 🤖 Available Commands\n\n"
            "| Command | Description |\n"
            "|---------|-------------|\n"
            "| `briefing` | Get your daily overview |\n"
            "| `schedule [minutes]` | Find available meeting times |\n"
            "| `tasks` | View prioritized tasks |\n"
            "| `inbox` | Summarize your emails |\n"
            "| `help` | Show this help message |\n\n"
            "You can also ask natural questions like:\n"
            "- *What's on my calendar today?*\n"
            "- *Do I have any urgent tasks?*\n"
            "- *Any important emails?*"
        )
    
    elif text in ["briefing", "brief", "daily", "morning", "overview"]:
        await context.send_activity("📊 Getting your daily briefing...")
        response = await assistant.get_daily_briefing()
        await context.send_activity(response)
    
    elif text.startswith("schedule") or text.startswith("meeting") or "find time" in text:
        # Extract duration if provided
        duration = 30
        words = text.split()
        for word in words:
            if word.isdigit():
                duration = int(word)
                break
        
        await context.send_activity(f"🔍 Finding {duration}-minute slots...")
        response = await assistant.find_meeting_time(duration)
        await context.send_activity(response)
    
    elif text in ["tasks", "todo", "todos", "priorities"]:
        await context.send_activity("✅ Getting your task priorities...")
        response = await assistant.get_task_priorities()
        await context.send_activity(response)
    
    elif text in ["inbox", "email", "emails", "mail"]:
        await context.send_activity("📧 Summarizing your inbox...")
        response = await assistant.summarize_inbox()
        await context.send_activity(response)
    
    elif "calendar" in text or "meeting" in text or "schedule" in text:
        await context.send_activity("📅 Getting your calendar...")
        response = await assistant.get_daily_briefing()
        await context.send_activity(response)
    
    else:
        # Default response for unrecognized input
        await context.send_activity(
            f"I received: *{context.activity.text}*\n\n"
            "I'm still learning! Try one of these commands:\n"
            "- `briefing` - Daily overview\n"
            "- `schedule` - Find meeting times\n"
            "- `tasks` - Prioritized tasks\n"
            "- `inbox` - Email summary\n"
            "- `help` - All commands"
        )
