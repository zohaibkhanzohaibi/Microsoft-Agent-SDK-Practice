# Personal Productivity Hub 🚀

A multi-agent system built with Microsoft 365 Agents SDK that helps manage your calendar, emails, and tasks using a 3-agent architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent C (Orchestrator)                    │
│              agents/assistant_agent/agent.py                 │
│                                                              │
│  Commands: briefing, schedule, tasks, inbox, help            │
└────────────────────┬────────────────────┬───────────────────┘
                     │                    │
         Uses MCP    │                    │   Calls tools
                     ▼                    ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│   Agent A (MCP Server)       │  │   Agent B (Scheduler)        │
│   Data Access Layer          │  │   Intelligence Layer         │
│   - get_user_profile         │  │   - find_available_slots     │
│   - get_calendar_events      │  │   - prioritize_tasks         │
│   - get_emails               │  │   - summarize_emails         │
│   - get_tasks                │  │   - draft_reply              │
└─────────────────────────────┘  └─────────────────────────────┘
```

## Prerequisites

- Python 3.12+
- Microsoft 365 Agents Playground (for local testing)
- Azure Entra App Registration (for M365 access)

## Quick Start

### 1. Activate the Virtual Environment

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt
.\.venv\Scripts\activate.bat
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```powershell
copy .env.example .env
```

For local testing without authentication, you can leave the values empty.

### 3. Run the Agent

```powershell
# Echo bot (basic)
python app.py

# Personal Productivity Hub (multi-agent)
python run_assistant.py
```

The agent will start on `http://localhost:3978`.

### 4. Test with Agents Playground

Open a new terminal and run:

```powershell
agentsplayground -e "http://localhost:3978/api/messages" -c "emulator"
```

## Commands

| Command | Description |
|---------|-------------|
| `briefing` | Get daily overview (calendar + emails + tasks) |
| `schedule [minutes]` | Find available meeting slots |
| `tasks` | View prioritized task list |
| `inbox` | Summarize your email inbox |
| `help` | Show all commands |

## Azure Entra Setup (Required for M365 Access)

1. Go to [https://entra.microsoft.com](https://entra.microsoft.com) → **App registrations** → **New registration**
2. Name: `Personal Productivity Hub`
3. Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
4. Add **API Permissions** (Delegated):
   - `User.Read`
   - `Calendars.Read`
   - `Mail.Read`
   - `Tasks.Read`
5. **Authentication** → Enable **"Allow public client flows"**
6. Copy **Application (client) ID** to `.env` as `M365_CLIENT_ID`

## Project Structure

```
├── agents/
│   ├── assistant_agent/      # Agent C - Orchestrator
│   │   └── agent.py          # Main personal assistant
│   ├── mcp_m365_server/      # Agent A - MCP Server
│   │   ├── graph_client.py   # Microsoft Graph API client
│   │   └── server.py         # MCP tool definitions
│   └── scheduler_agent/      # Agent B - Scheduler Tools
│       └── agent.py          # Scheduling & prioritization
├── config/
│   └── graph_auth.py         # MSAL authentication
├── .env                      # Environment variables (git-ignored)
├── .env.example              # Environment template
├── app.py                    # Simple echo bot
├── run_assistant.py          # Multi-agent entry point
├── start_server.py           # Server configuration
└── requirements.txt          # Python dependencies
```

## Installed Packages

| Package | Description |
|---------|-------------|
| `microsoft-agents-activity` | Activity protocol types |
| `microsoft-agents-hosting-core` | Core hosting library |
| `microsoft-agents-hosting-aiohttp` | aiohttp server integration |
| `microsoft-agents-authentication-msal` | MSAL authentication |
| `microsoft-agents-hosting-teams` | Teams channel support |
| `microsoft-agents-copilotstudio-client` | Copilot Studio integration |
| `mcp` | Model Context Protocol |
| `msal` | Microsoft Authentication Library |
| `msgraph-sdk` | Microsoft Graph API SDK |

## The 3 Agents Explained

### Agent A - MCP M365 Server
**Purpose:** Data access layer for Microsoft 365  
**Location:** `agents/mcp_m365_server/`  
**Protocol:** Model Context Protocol (MCP)  
**Tools:** `get_user_profile`, `get_calendar_events`, `get_emails`, `get_tasks`

### Agent B - Scheduler Tool  
**Purpose:** Intelligence layer for analysis  
**Location:** `agents/scheduler_agent/`  
**Functions:** `find_available_slots`, `prioritize_tasks`, `summarize_emails`, `draft_reply`

### Agent C - Personal Assistant (Orchestrator)
**Purpose:** User-facing agent that combines A & B  
**Location:** `agents/assistant_agent/`  
**Entry Point:** `run_assistant.py`

## Documentation

- [Microsoft 365 Agents SDK Docs](https://aka.ms/M365-Agents-SDK-Docs)
- [Python Quickstart](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/quickstart-python)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/overview)
