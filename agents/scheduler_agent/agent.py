"""
Scheduler Agent - Tool Agent for Personal Productivity Hub
Provides scheduling, prioritization, and email analysis functions
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json


class SchedulerAgent:
    """
    Tool agent that provides scheduling and productivity functions.
    Can be called by the orchestrator agent to process M365 data.
    """
    
    def find_available_slots(
        self,
        calendar_events: List[Dict[str, Any]],
        duration_minutes: int = 30,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        working_hours_start: int = 9,
        working_hours_end: int = 17,
    ) -> List[Dict[str, str]]:
        """
        Find available time slots in the calendar.
        
        Args:
            calendar_events: List of calendar events from MCP server
            duration_minutes: Required meeting duration
            start_date: Start date (YYYY-MM-DD), defaults to today
            end_date: End date (YYYY-MM-DD), defaults to 5 business days
            working_hours_start: Start of working day (hour)
            working_hours_end: End of working day (hour)
            
        Returns:
            List of available time slots with start and end times
        """
        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now().replace(hour=working_hours_start, minute=0, second=0, microsecond=0)
            if datetime.now().hour >= working_hours_start:
                start = start + timedelta(days=1)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = start + timedelta(days=5)
        
        # Parse existing events into busy slots
        busy_slots = []
        for event in calendar_events:
            if event.get("start") and event.get("end"):
                try:
                    event_start = datetime.fromisoformat(event["start"].replace("Z", ""))
                    event_end = datetime.fromisoformat(event["end"].replace("Z", ""))
                    busy_slots.append((event_start, event_end))
                except (ValueError, TypeError):
                    continue
        
        busy_slots.sort(key=lambda x: x[0])
        
        # Find available slots
        available_slots = []
        current = start
        duration = timedelta(minutes=duration_minutes)
        
        while current < end and len(available_slots) < 10:
            # Skip weekends
            if current.weekday() >= 5:
                current = current + timedelta(days=1)
                current = current.replace(hour=working_hours_start, minute=0)
                continue
            
            # Check if within working hours
            if current.hour < working_hours_start:
                current = current.replace(hour=working_hours_start, minute=0)
            elif current.hour >= working_hours_end:
                current = current + timedelta(days=1)
                current = current.replace(hour=working_hours_start, minute=0)
                continue
            
            slot_end = current + duration
            
            # Check if slot conflicts with any busy period
            is_available = True
            for busy_start, busy_end in busy_slots:
                if not (slot_end <= busy_start or current >= busy_end):
                    is_available = False
                    # Move current to end of busy slot
                    current = busy_end
                    break
            
            if is_available:
                if slot_end.hour <= working_hours_end:
                    available_slots.append({
                        "start": current.isoformat(),
                        "end": slot_end.isoformat(),
                        "duration_minutes": duration_minutes,
                        "day": current.strftime("%A, %B %d"),
                    })
                current = slot_end
            
        return available_slots
    
    def prioritize_tasks(
        self,
        tasks: List[Dict[str, Any]],
        criteria: str = "urgency"
    ) -> List[Dict[str, Any]]:
        """
        Prioritize tasks based on given criteria.
        
        Args:
            tasks: List of tasks from MCP server
            criteria: Prioritization criteria - "urgency", "importance", or "balanced"
            
        Returns:
            Sorted list of tasks with priority scores and recommendations
        """
        prioritized = []
        now = datetime.now()
        
        for task in tasks:
            score = 0
            reasons = []
            
            # Skip completed tasks
            if task.get("status") == "completed":
                continue
            
            # Importance scoring
            importance = task.get("importance", "normal")
            if importance == "high":
                score += 30
                reasons.append("High importance")
            elif importance == "low":
                score -= 10
            
            # Due date scoring
            due_date_str = task.get("dueDate")
            if due_date_str:
                try:
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", ""))
                    days_until_due = (due_date - now).days
                    
                    if days_until_due < 0:
                        score += 50
                        reasons.append(f"OVERDUE by {abs(days_until_due)} days")
                    elif days_until_due == 0:
                        score += 40
                        reasons.append("Due TODAY")
                    elif days_until_due <= 2:
                        score += 30
                        reasons.append(f"Due in {days_until_due} days")
                    elif days_until_due <= 7:
                        score += 15
                        reasons.append(f"Due this week")
                except (ValueError, TypeError):
                    pass
            
            # Adjust based on criteria
            if criteria == "importance":
                # Boost importance weight
                if importance == "high":
                    score += 20
            elif criteria == "urgency":
                # Already weighted towards due dates
                pass
            
            prioritized.append({
                **task,
                "priority_score": score,
                "priority_reasons": reasons,
                "recommendation": self._get_task_recommendation(score, reasons),
            })
        
        # Sort by priority score descending
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return prioritized
    
    def _get_task_recommendation(self, score: int, reasons: List[str]) -> str:
        """Generate a recommendation based on priority score."""
        if score >= 50:
            return "🔴 Do this immediately"
        elif score >= 30:
            return "🟠 High priority - tackle today"
        elif score >= 15:
            return "🟡 Schedule time this week"
        else:
            return "🟢 Can wait - schedule when convenient"
    
    def summarize_emails(
        self,
        emails: List[Dict[str, Any]],
        filter_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Summarize and categorize emails.
        
        Args:
            emails: List of emails from MCP server
            filter_type: "all", "unread", or "important"
            
        Returns:
            Summary with counts, categories, and action items
        """
        # Filter emails
        if filter_type == "unread":
            emails = [e for e in emails if not e.get("isRead")]
        elif filter_type == "important":
            emails = [e for e in emails if e.get("importance") == "high"]
        
        # Categorize
        categories = {
            "action_required": [],
            "fyi": [],
            "meetings": [],
            "other": [],
        }
        
        action_keywords = ["please", "action", "required", "urgent", "asap", "deadline", "review", "approve"]
        meeting_keywords = ["meeting", "invite", "calendar", "schedule", "call", "sync"]
        
        for email in emails:
            subject = (email.get("subject") or "").lower()
            preview = (email.get("preview") or "").lower()
            combined = subject + " " + preview
            
            if any(kw in combined for kw in meeting_keywords):
                categories["meetings"].append(email)
            elif any(kw in combined for kw in action_keywords):
                categories["action_required"].append(email)
            elif email.get("importance") == "high":
                categories["action_required"].append(email)
            else:
                categories["fyi"].append(email)
        
        return {
            "total_count": len(emails),
            "unread_count": sum(1 for e in emails if not e.get("isRead")),
            "important_count": sum(1 for e in emails if e.get("importance") == "high"),
            "categories": {
                "action_required": {
                    "count": len(categories["action_required"]),
                    "emails": categories["action_required"][:5],
                },
                "meetings": {
                    "count": len(categories["meetings"]),
                    "emails": categories["meetings"][:5],
                },
                "fyi": {
                    "count": len(categories["fyi"]),
                    "emails": categories["fyi"][:5],
                },
            },
            "summary": self._generate_email_summary(categories),
        }
    
    def _generate_email_summary(self, categories: Dict) -> str:
        """Generate a human-readable email summary."""
        parts = []
        
        action_count = len(categories["action_required"])
        if action_count > 0:
            parts.append(f"📌 {action_count} email(s) need your attention")
        
        meeting_count = len(categories["meetings"])
        if meeting_count > 0:
            parts.append(f"📅 {meeting_count} meeting-related email(s)")
        
        fyi_count = len(categories["fyi"])
        if fyi_count > 0:
            parts.append(f"📧 {fyi_count} FYI email(s)")
        
        if not parts:
            return "Your inbox is clear! 🎉"
        
        return " | ".join(parts)
    
    def draft_reply(
        self,
        email: Dict[str, Any],
        tone: str = "professional",
        intent: str = "acknowledge"
    ) -> Dict[str, str]:
        """
        Draft a reply to an email.
        
        Args:
            email: Email to reply to (from MCP server)
            tone: "professional", "friendly", or "brief"
            intent: "acknowledge", "decline", "accept", or "follow_up"
            
        Returns:
            Draft reply with subject and body
        """
        sender_name = email.get("from", "").split()[0] if email.get("from") else "there"
        subject = email.get("subject", "your email")
        
        # Greeting based on tone
        greetings = {
            "professional": f"Dear {sender_name},",
            "friendly": f"Hi {sender_name}!",
            "brief": f"Hi {sender_name},",
        }
        greeting = greetings.get(tone, greetings["professional"])
        
        # Body based on intent
        bodies = {
            "acknowledge": f"Thank you for your email regarding \"{subject}\". I have received it and will review the details. I'll get back to you shortly with a more detailed response.",
            "decline": f"Thank you for reaching out regarding \"{subject}\". After careful consideration, I'm afraid I won't be able to proceed with this at the moment. I appreciate your understanding.",
            "accept": f"Thank you for your email regarding \"{subject}\". I'm happy to confirm my acceptance and look forward to moving ahead. Please let me know if you need any additional information from my end.",
            "follow_up": f"I wanted to follow up on your previous email regarding \"{subject}\". Please let me know if there are any updates or if you need anything from me to move forward.",
        }
        body = bodies.get(intent, bodies["acknowledge"])
        
        # Closing based on tone
        closings = {
            "professional": "Best regards,",
            "friendly": "Cheers,",
            "brief": "Thanks,",
        }
        closing = closings.get(tone, closings["professional"])
        
        return {
            "to": email.get("fromEmail", ""),
            "subject": f"Re: {subject}",
            "body": f"{greeting}\n\n{body}\n\n{closing}",
            "tone": tone,
            "intent": intent,
        }


# Singleton instance
_scheduler: Optional[SchedulerAgent] = None


def get_scheduler() -> SchedulerAgent:
    """Get the singleton scheduler agent instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerAgent()
    return _scheduler
