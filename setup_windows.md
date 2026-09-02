# Agent Harness --- Windows Setup Guide

This guide walks through the complete Windows setup for the **Agent
Harness**.

The automated setup script installs and configures the main dependencies
required by the project:

-   Git
-   Python 3.11+
-   Python virtual environment
-   Python packages from `requirements.txt`
-   Ollama
-   PostgreSQL
-   `.env` from `.env.example`, when available

The setup script intentionally **does not pull the Ollama model** and
**does not configure private credentials such as your LangSmith API
key**. Those steps are completed manually after automated setup.

------------------------------------------------------------------------

## 1. Requirements

Before starting, make sure you have:

-   Windows 10 or Windows 11
-   Internet access
-   PowerShell
-   Administrator access to your computer
-   Enough free disk space for PostgreSQL, Ollama, the required model,
    and the project

You do **not** need to manually install Python, Git, PostgreSQL, or
Ollama before running the setup script.

------------------------------------------------------------------------

## 2. Open PowerShell

Open the Windows Start menu, search for **PowerShell**, and choose **Run
as Administrator** for the initial setup.

------------------------------------------------------------------------

## 3. Check `winget`

The setup script uses Windows Package Manager.

``` powershell
winget --version
```

If `winget` is not recognized, install or update **App Installer** from
the Microsoft Store, restart PowerShell, and run the command again.

------------------------------------------------------------------------

## 4. Clone the Repository

Navigate to the directory where you want the project.

``` powershell
cd $HOME\Desktop
```

Clone the repository:

``` powershell
git clone https://github.com/Harsh-Sharma-2002/Agentic-harnesss
```

Enter it:

``` powershell
cd Agent_Harness
```

Verify:

``` powershell
Get-Location
```

All remaining commands assume you are in the repository root.

------------------------------------------------------------------------

## 5. Allow the Setup Script to Run

For the current PowerShell session only:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This does not permanently change your Windows execution policy.

------------------------------------------------------------------------

## 6. Run Automated Setup

``` powershell
.\scripts\setup.ps1
```

The script performs:

``` text
Check winget
      ↓
Install / verify Git
      ↓
Install / verify Python 3.11+
      ↓
Install / verify Ollama
      ↓
Install / verify PostgreSQL
      ↓
Create .venv
      ↓
Upgrade pip / setuptools / wheel
      ↓
Install requirements.txt
      ↓
Create .env from .env.example
      ↓
Verify dependencies
```

Do not close PowerShell while setup is running. The script is designed
to be rerunnable if setup is interrupted.

------------------------------------------------------------------------

## 7. PostgreSQL Installation Prompt

The PostgreSQL Windows installer may require configuration.

The default administrative user is:

``` text
postgres
```

If asked to create a password for this account, choose one you can
remember and keep it available. It may be needed later when initializing
the project database.

The Agent Harness should **not** use this administrator account for
normal Text2SQL execution.

> Simple classroom passwords are acceptable only for disposable local
> development environments. Do not use them in production.

------------------------------------------------------------------------

## 8. Restart PowerShell If Necessary

Windows installers may update `PATH` only for new terminal sessions.

If setup says Python, Git, Ollama, or PostgreSQL was installed but
cannot be found:

1.  Close PowerShell.
2.  Open a new PowerShell window.
3.  Return to the repository.
4.  Allow script execution.
5.  Rerun setup.

``` powershell
cd $HOME\Desktop\Agent_Harness
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
```

Already-installed dependencies should be detected and reused.

------------------------------------------------------------------------

## 9. Activate the Virtual Environment

The setup script creates `.venv`.

``` powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should now look similar to:

``` text
(.venv) PS C:\Users\YourName\Desktop\Agent_Harness>
```

Activate this environment whenever you open a new terminal for the
project.

------------------------------------------------------------------------

## 10. Verify Python

``` powershell
python --version
python -m pip --version
```

The project requires **Python 3.11 or newer**.

------------------------------------------------------------------------

## 11. Verify Python Dependencies

LangGraph:

``` powershell
python -c "import langgraph; print('LangGraph OK')"
```

LangChain:

``` powershell
python -c "import langchain_core; print('LangChain OK')"
```

FastAPI:

``` powershell
python -c "import fastapi; print('FastAPI OK')"
```

Streamlit:

``` powershell
python -c "import streamlit; print('Streamlit OK')"
```

------------------------------------------------------------------------

## 12. Verify Ollama

``` powershell
ollama --version
```

If `ollama` cannot be found immediately after installation, restart
PowerShell.

------------------------------------------------------------------------

## 13. Start Ollama

``` powershell
ollama serve
```

Keep this terminal open while using the Agent Harness.

The default Ollama endpoint is:

``` text
http://localhost:11434
```

If Ollama reports that the address is already in use, it may already be
running. Verify from another terminal with:

``` powershell
ollama list
```

------------------------------------------------------------------------

## 14. Open a Second PowerShell Window

Leave Ollama running.

In another PowerShell window:

``` powershell
cd $HOME\Desktop\Agent_Harness
.\.venv\Scripts\Activate.ps1
```

If execution policy blocks activation:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

------------------------------------------------------------------------

## 15. Pull the Required Ollama Model

The setup script intentionally does **not** download a model.

``` powershell
ollama pull <MODEL_NAME>
```

Replace `<MODEL_NAME>` with the exact model specified for the course.

Example:

``` powershell
ollama pull qwen3.5:4b
```

------------------------------------------------------------------------

## 16. Verify the Model

``` powershell
ollama list
```

Optional direct test:

``` powershell
ollama run <MODEL_NAME>
```

Enter a simple prompt such as `Hello`.

Exit with:

``` text
/bye
```

------------------------------------------------------------------------

## 17. Configure `.env`

The setup script creates `.env` from `.env.example` when possible.

Open `.env` in your editor. With VS Code:

``` powershell
code .env
```

If `code` is unavailable, open the file manually.

**Never commit `.env` to Git.**

------------------------------------------------------------------------

## 18. Configure Ollama

Add or update:

``` dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=<MODEL_NAME>
```

Example:

``` dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
```

The model name must exactly match `ollama list`.

------------------------------------------------------------------------

## 19. Configure LangSmith

Add:

``` dotenv
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agent-harness
LANGSMITH_API_KEY=<YOUR_LANGSMITH_API_KEY>
```

Use your own authorized LangSmith API key.

**Never commit or share the API key.**

------------------------------------------------------------------------

## 20. Verify PostgreSQL

``` powershell
psql --version
```

If `psql` is not recognized immediately after installation, restart
PowerShell and try again.

------------------------------------------------------------------------

## 21. Verify the PostgreSQL Service

``` powershell
Get-Service | Where-Object {$_.Name -like "postgresql*"}
```

The service should normally show:

``` text
Running
```

If stopped, open Administrator PowerShell and run:

``` powershell
Start-Service <SERVICE_NAME>
```

Replace `<SERVICE_NAME>` with the service name shown by the previous
command.

------------------------------------------------------------------------

## 22. Test the PostgreSQL Administrator Connection

``` powershell
psql -U postgres
```

Enter the PostgreSQL administrator password if prompted.

A successful connection gives a prompt similar to:

``` text
postgres=#
```

Exit with:

``` sql
\q
```

------------------------------------------------------------------------

## 23. Project Database Credentials

Normal Text2SQL execution should use a dedicated local project account
rather than the `postgres` administrator.

Recommended local development values:

``` dotenv
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=agent_harness
DATABASE_USER=agent_harness
DATABASE_PASSWORD=agent_harness_dev
```

These values are intended only for a local classroom/development
environment.

The database initialization process should create the matching database
and account.

------------------------------------------------------------------------

## 24. Why Use a Separate Database Account?

The `postgres` account has administrative privileges. The agent should
not need those privileges.

``` text
PostgreSQL Administrator
        |
        +-- Agent Harness database
                |
                +-- Agent Harness account
                        |
                        +-- limited project permissions
```

This follows **least privilege**: give each component only the
permissions required to perform its job.

For Text2SQL, the runtime account should eventually be limited to the
schemas, tables, and operations the agent actually requires.

------------------------------------------------------------------------

## 25. Final `.env` Shape

Your `.env` should eventually contain values similar to:

``` dotenv
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=<MODEL_NAME>

# LangSmith
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agent-harness
LANGSMITH_API_KEY=<YOUR_LANGSMITH_API_KEY>

# PostgreSQL
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=agent_harness
DATABASE_USER=agent_harness
DATABASE_PASSWORD=agent_harness_dev
```

Replace placeholders with the values specified for the course/project.

------------------------------------------------------------------------

## 26. Normal Startup on Future Sessions

You do not need to reinstall dependencies every time.

### Terminal 1 --- Ollama

``` powershell
ollama serve
```

Keep it open.

### Terminal 2 --- Agent Harness

``` powershell
cd <PATH_TO_AGENT_HARNESS>
.\.venv\Scripts\Activate.ps1
```

Then start the Agent Harness using the project's normal startup command.

------------------------------------------------------------------------

# Troubleshooting

## 27. PowerShell Blocks a Script

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then retry setup:

``` powershell
.\scripts\setup.ps1
```

or activation:

``` powershell
.\.venv\Scripts\Activate.ps1
```

------------------------------------------------------------------------

## 28. Command Not Found After Installation

If any of these are unavailable:

``` text
git
python
ollama
psql
```

close PowerShell and open a new session.

Then return to the repository and rerun:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
```

------------------------------------------------------------------------

## 29. Ollama Is Not Responding

Check:

``` powershell
ollama list
```

If needed:

``` powershell
ollama serve
```

Confirm `.env` contains:

``` dotenv
OLLAMA_BASE_URL=http://localhost:11434
```

------------------------------------------------------------------------

## 30. Ollama Model Not Found

``` powershell
ollama list
```

If missing:

``` powershell
ollama pull <MODEL_NAME>
```

Make sure `.env` uses the exact same name:

``` dotenv
OLLAMA_MODEL=<MODEL_NAME>
```

------------------------------------------------------------------------

## 31. PostgreSQL Connection Fails

Check the service:

``` powershell
Get-Service | Where-Object {$_.Name -like "postgresql*"}
```

Test the administrator connection:

``` powershell
psql -U postgres
```

For project-account problems, verify:

``` text
DATABASE_HOST
DATABASE_PORT
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD
```

in `.env`.

------------------------------------------------------------------------

## 32. Python Package Missing

Confirm the prompt begins with:

``` text
(.venv)
```

Then reinstall:

``` powershell
python -m pip install -r requirements.txt
```

Verify LangGraph:

``` powershell
python -c "import langgraph; print('LangGraph OK')"
```

------------------------------------------------------------------------

## 33. `.env` Was Not Created

If `.env.example` exists:

``` powershell
Copy-Item .env.example .env
```

Then edit `.env`.

------------------------------------------------------------------------

## 34. Setup Was Interrupted

Rerun:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
```

The setup script should reuse installed dependencies, the existing
`.venv`, and the existing `.env`.

------------------------------------------------------------------------

# Security Notes

## 35. Never Commit `.env`

Verify `.gitignore` contains:

``` gitignore
.env
```

`.env` may contain API keys, database credentials, and local
configuration.

------------------------------------------------------------------------

## 36. Never Share API Keys

Do not publish:

``` text
LANGSMITH_API_KEY
```

If a key is accidentally exposed, revoke it and create a new one.

------------------------------------------------------------------------

## 37. Do Not Run the Agent as PostgreSQL Administrator

The `postgres` account is for administration.

Normal Text2SQL execution should use a dedicated project account with
limited permissions.

------------------------------------------------------------------------

# Final Setup Checklist

Before running the full Agent Harness, verify:

``` text
[ ] Repository cloned
[ ] setup.ps1 completed
[ ] Git installed
[ ] Python 3.11+ installed
[ ] .venv created
[ ] .venv activated
[ ] requirements.txt installed
[ ] Ollama installed
[ ] Ollama server running
[ ] Required Ollama model downloaded
[ ] .env created
[ ] Ollama values configured
[ ] LangSmith API key configured
[ ] PostgreSQL installed
[ ] PostgreSQL service running
[ ] PostgreSQL administrator connection tested
[ ] Project database/account initialized
[ ] Project database values configured in .env
```

Once all required items are complete, the Windows environment is ready
for the Agent Harness.
