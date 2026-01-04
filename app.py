"""
Microsoft 365 Agents SDK - Echo Agent
A simple agent that echoes back user messages.
"""

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from start_server import start_server


AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(), adapter=CloudAdapter()
)


async def _help(context: TurnContext, _: TurnState):
    await context.send_activity(
        "Welcome to the Microsoft 365 Agents SDK Echo Bot! "
        "Type anything and I'll echo it back to you."
    )


AGENT_APP.conversation_update("membersAdded")(_help)


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _):
    await context.send_activity(f"You said: {context.activity.text}")


if __name__ == "__main__":
    try:
        start_server(AGENT_APP, None)
    except Exception as error:
        raise error
