"""
Personal Productivity Hub - Main Entry Point
Runs the multi-agent Personal Assistant system.
"""

from dotenv import load_dotenv
load_dotenv()

from agents.assistant_agent.agent import AGENT_APP
from start_server import start_server


if __name__ == "__main__":
    print("=" * 60)
    print("  Personal Productivity Hub - Multi-Agent System")
    print("=" * 60)
    print()
    print("Architecture:")
    print("  - Agent A (MCP Server): Microsoft 365 data access")
    print("  - Agent B (Scheduler): Scheduling & prioritization tools")
    print("  - Agent C (Orchestrator): Personal Assistant that combines A & B")
    print()
    print("Before using, ensure you have:")
    print("  1. Created an Azure Entra app registration")
    print("  2. Set M365_CLIENT_ID in your .env file")
    print("  3. Granted delegated permissions: User.Read, Calendars.Read,")
    print("     Mail.Read, Tasks.Read")
    print()
    
    try:
        start_server(AGENT_APP, None)
    except Exception as error:
        raise error
