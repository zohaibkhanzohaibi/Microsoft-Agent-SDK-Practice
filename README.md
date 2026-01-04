# Microsoft 365 Agents SDK - Python Project

A Python project template for building agents using the Microsoft 365 Agents SDK that can be deployed to Copilot Studio or integrated with Microsoft Teams.

## Prerequisites

- Python 3.12+
- Microsoft 365 Agents Playground (for local testing)
- Azure subscription (for deployment)

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
python app.py
```

The agent will start on `http://localhost:3978`.

### 4. Test with Agents Playground

Open a new terminal and run:

```powershell
agentsplayground -e "http://localhost:3978/api/messages" -c "emulator"
```

## Available Commands

| Command | Description |
|---------|-------------|
| `python app.py` | Start the agent server |
| `pip install -r requirements.txt` | Install dependencies |
| `agentsplayground -e "http://localhost:3978/api/messages" -c "emulator"` | Test with Agents Playground |

## Project Structure

```
├── .env                  # Environment variables (git-ignored)
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
├── app.py                # Agent logic (EchoAgent)
├── start_server.py       # Server configuration
└── README.md             # This file
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

## Copilot Studio Integration

To connect your agent to Copilot Studio:

1. Create an Agent in [Copilot Studio](https://copilotstudio.microsoft.com/)
2. Create an Azure App Registration with `CopilotStudio.Copilots.Invoke` permission
3. Fill in the Copilot Studio environment variables in `.env`

## Deployment Options

- **Azure Bot Service**: Deploy with Azure Bot registration
- **Microsoft Teams**: Publish through Teams App manifest
- **Copilot Studio**: Integrate as a custom agent

## Documentation

- [Microsoft 365 Agents SDK Docs](https://aka.ms/M365-Agents-SDK-Docs)
- [Python Quickstart](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/quickstart-python)
- [GitHub Samples](https://github.com/microsoft/Agents/tree/main/samples/python)
