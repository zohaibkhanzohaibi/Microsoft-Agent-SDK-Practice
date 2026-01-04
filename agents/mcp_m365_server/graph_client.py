"""
Microsoft Graph API Client
Provides read-only access to Calendar, Mail, and Tasks
"""

import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.graph_auth import get_access_token


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


class GraphClient:
    """Async client for Microsoft Graph API."""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with auth headers."""
        if self._session is None or self._session.closed:
            token = get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request to Graph API."""
        session = await self._get_session()
        url = f"{GRAPH_BASE_URL}{endpoint}"
        async with session.get(url, params=params) as response:
            if response.status == 401:
                # Token expired, refresh and retry
                await self.close()
                self._session = None
                session = await self._get_session()
                async with session.get(url, params=params) as retry_response:
                    retry_response.raise_for_status()
                    return await retry_response.json()
            response.raise_for_status()
            return await response.json()
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """Get the current user's profile."""
        result = await self._get("/me")
        return {
            "id": result.get("id"),
            "displayName": result.get("displayName"),
            "mail": result.get("mail") or result.get("userPrincipalName"),
            "jobTitle": result.get("jobTitle"),
            "officeLocation": result.get("officeLocation"),
        }
    
    async def get_calendar_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events within a date range.
        
        Args:
            start_date: ISO format date string (default: today)
            end_date: ISO format date string (default: 7 days from start)
            max_results: Maximum number of events to return
        """
        if not start_date:
            start_date = datetime.utcnow().isoformat() + "Z"
        if not end_date:
            end_dt = datetime.utcnow() + timedelta(days=7)
            end_date = end_dt.isoformat() + "Z"
        
        params = {
            "$filter": f"start/dateTime ge '{start_date}' and end/dateTime le '{end_date}'",
            "$orderby": "start/dateTime",
            "$top": str(max_results),
            "$select": "id,subject,start,end,location,attendees,isAllDay,organizer",
        }
        
        result = await self._get("/me/events", params)
        events = result.get("value", [])
        
        return [
            {
                "id": event.get("id"),
                "subject": event.get("subject"),
                "start": event.get("start", {}).get("dateTime"),
                "end": event.get("end", {}).get("dateTime"),
                "location": event.get("location", {}).get("displayName"),
                "isAllDay": event.get("isAllDay"),
                "organizer": event.get("organizer", {}).get("emailAddress", {}).get("name"),
                "attendees": [
                    a.get("emailAddress", {}).get("name")
                    for a in event.get("attendees", [])
                ],
            }
            for event in events
        ]
    
    async def get_emails(
        self,
        folder: str = "inbox",
        unread_only: bool = False,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get emails from a folder.
        
        Args:
            folder: Mail folder (inbox, sentitems, drafts)
            unread_only: Only return unread emails
            max_results: Maximum number of emails to return
        """
        params = {
            "$orderby": "receivedDateTime desc",
            "$top": str(max_results),
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview,importance",
        }
        
        if unread_only:
            params["$filter"] = "isRead eq false"
        
        endpoint = f"/me/mailFolders/{folder}/messages"
        result = await self._get(endpoint, params)
        emails = result.get("value", [])
        
        return [
            {
                "id": email.get("id"),
                "subject": email.get("subject"),
                "from": email.get("from", {}).get("emailAddress", {}).get("name"),
                "fromEmail": email.get("from", {}).get("emailAddress", {}).get("address"),
                "receivedDateTime": email.get("receivedDateTime"),
                "isRead": email.get("isRead"),
                "preview": email.get("bodyPreview", "")[:200],
                "importance": email.get("importance"),
            }
            for email in emails
        ]
    
    async def get_tasks(
        self,
        list_name: Optional[str] = None,
        include_completed: bool = False,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get tasks from Microsoft To Do.
        
        Args:
            list_name: Name of task list (default: all lists)
            include_completed: Include completed tasks
            max_results: Maximum number of tasks to return
        """
        # First get task lists
        lists_result = await self._get("/me/todo/lists")
        task_lists = lists_result.get("value", [])
        
        all_tasks = []
        
        for task_list in task_lists:
            if list_name and task_list.get("displayName") != list_name:
                continue
            
            list_id = task_list.get("id")
            list_display_name = task_list.get("displayName")
            
            params = {
                "$top": str(max_results),
                "$orderby": "importance desc,dueDateTime/dateTime asc",
            }
            
            if not include_completed:
                params["$filter"] = "status ne 'completed'"
            
            tasks_result = await self._get(f"/me/todo/lists/{list_id}/tasks", params)
            tasks = tasks_result.get("value", [])
            
            for task in tasks:
                due_date = None
                if task.get("dueDateTime"):
                    due_date = task["dueDateTime"].get("dateTime")
                
                all_tasks.append({
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "listName": list_display_name,
                    "status": task.get("status"),
                    "importance": task.get("importance"),
                    "dueDate": due_date,
                    "body": task.get("body", {}).get("content", "")[:200],
                })
        
        return all_tasks[:max_results]


# Singleton instance
_client: Optional[GraphClient] = None


def get_graph_client() -> GraphClient:
    """Get the singleton Graph client instance."""
    global _client
    if _client is None:
        _client = GraphClient()
    return _client
