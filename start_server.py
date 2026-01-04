"""
Microsoft 365 Agents SDK - Server Entry Point
Configures and starts the aiohttp server for the agent.
"""

import os
import asyncio
from dotenv import load_dotenv
from aiohttp import web

from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalAuth

from app import EchoAgent

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv("PORT", 3978))
HOST = os.getenv("HOST", "localhost")
BOT_APP_ID = os.getenv("BOT_APP_ID", "")
BOT_APP_PASSWORD = os.getenv("BOT_APP_PASSWORD", "")
BOT_TENANT_ID = os.getenv("BOT_TENANT_ID", "")


def create_adapter() -> CloudAdapter:
    """
    Create and configure the bot adapter.

    For local development without authentication (using Agents Playground),
    the adapter can be created without credentials.

    For production or testing with Azure Bot Service,
    configure BOT_APP_ID, BOT_APP_PASSWORD, and BOT_TENANT_ID.
    """
    if BOT_APP_ID and BOT_APP_PASSWORD:
        # Production mode with authentication
        auth = MsalAuth(
            app_id=BOT_APP_ID,
            app_password=BOT_APP_PASSWORD,
            tenant_id=BOT_TENANT_ID or "botframework.com",
        )
        return CloudAdapter(auth=auth)
    else:
        # Development mode without authentication
        # Use with Agents Playground: agentsplayground -e "http://localhost:3978/api/messages" -c "emulator"
        return CloudAdapter()


# Create the adapter and agent
adapter = create_adapter()
agent = EchoAgent()


async def messages(request: web.Request) -> web.Response:
    """
    Handle incoming messages from the Bot Framework or Agents Playground.

    This is the main endpoint that receives activities from channels.
    """
    body = await request.json()
    auth_header = request.headers.get("Authorization", "")

    response = await adapter.process_activity(body, auth_header, agent.on_turn)

    if response:
        return web.json_response(response.body, status=response.status)
    return web.Response(status=200)


async def health(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "agent": "EchoAgent"})


def create_app() -> web.Application:
    """Create and configure the aiohttp web application."""
    app = web.Application()
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/health", health)
    app.router.add_get("/", health)
    return app


def main():
    """Start the agent server."""
    print(f"Starting agent server on http://{HOST}:{PORT}")
    print(f"Messages endpoint: http://{HOST}:{PORT}/api/messages")
    print(f"Health endpoint: http://{HOST}:{PORT}/health")
    print()
    print("To test with Agents Playground, run:")
    print(f'  agentsplayground -e "http://{HOST}:{PORT}/api/messages" -c "emulator"')
    print()

    app = create_app()
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
