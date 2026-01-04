"""
Microsoft 365 Agents SDK - Echo Agent
A simple agent that echoes back user messages.
"""

from microsoft_agents.hosting.core import (
    Agent,
    TurnContext,
)
from microsoft_agents.activity import Activity, ActivityTypes


class EchoAgent(Agent):
    """
    A simple echo agent that responds to user messages.
    This serves as a starting template for building more complex agents.
    """

    async def on_turn(self, turn_context: TurnContext) -> None:
        """
        Handle incoming activities.

        Args:
            turn_context: The context object for this turn.
        """
        if turn_context.activity.type == ActivityTypes.message:
            # Echo back the user's message
            user_message = turn_context.activity.text
            reply_text = f"You said: {user_message}"
            await turn_context.send_activity(Activity(type=ActivityTypes.message, text=reply_text))

        elif turn_context.activity.type == ActivityTypes.conversation_update:
            # Handle members being added to the conversation
            await self._handle_conversation_update(turn_context)

    async def _handle_conversation_update(self, turn_context: TurnContext) -> None:
        """
        Handle conversation update activities (e.g., new members joining).

        Args:
            turn_context: The context object for this turn.
        """
        if turn_context.activity.members_added:
            for member in turn_context.activity.members_added:
                if member.id != turn_context.activity.recipient.id:
                    welcome_text = (
                        "Welcome to the Microsoft 365 Agents SDK Echo Bot! "
                        "Type anything and I'll echo it back to you."
                    )
                    await turn_context.send_activity(
                        Activity(type=ActivityTypes.message, text=welcome_text)
                    )
