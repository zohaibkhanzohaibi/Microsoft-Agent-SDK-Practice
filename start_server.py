"""
Microsoft 365 Agents SDK - Server Entry Point
Configures and starts the aiohttp server for the agent.
"""

from os import environ
from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration
from microsoft_agents.hosting.aiohttp import (
    start_agent_process,
    jwt_authorization_middleware,
    CloudAdapter,
)
from aiohttp.web import Request, Response, Application, run_app


def start_server(
    agent_application: AgentApplication, auth_configuration: AgentAuthConfiguration
):
    async def entry_point(req: Request) -> Response:
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]
        return await start_agent_process(
            req,
            agent,
            adapter,
        )

    APP = Application(middlewares=[jwt_authorization_middleware])
    APP.router.add_post("/api/messages", entry_point)
    APP.router.add_get("/api/messages", lambda _: Response(status=200))
    APP["agent_configuration"] = auth_configuration
    APP["agent_app"] = agent_application
    APP["adapter"] = agent_application.adapter

    port = int(environ.get("PORT", 3978))
    print(f"Starting agent server on http://localhost:{port}")
    print(f"Messages endpoint: http://localhost:{port}/api/messages")
    print()
    print("To test with Agents Playground, run:")
    print(f'  agentsplayground -e "http://localhost:{port}/api/messages" -c "emulator"')
    print()

    try:
        run_app(APP, host="localhost", port=port)
    except Exception as error:
        raise error
