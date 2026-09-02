# Agent Harness --- macOS / Linux Setup Guide

This guide walks through the complete macOS and Linux setup for the
**Agent Harness**.

The automated setup script installs and configures the main dependencies
required by the project:

-   Git
-   curl
-   Python 3.11+
-   Python virtual environment
-   Python packages from `requirements.txt`
-   Ollama
-   PostgreSQL
-   `.env` from `.env.example`, when available

On macOS, the script uses **Homebrew** and installs Homebrew if it is
not already available.

On Linux, the script detects a supported package manager such as `apt`,
`dnf`, `yum`, or `pacman`.

The setup script intentionally **does not pull the Ollama model** and
**does not configure private credentials such as your LangSmith API
key**. Those steps are completed manually after automated setup.

------------------------------------------------------------------------

## 1. Requirements

Before starting, make sure you have:

-   macOS or a supported Linux distribution
-   Internet access
-   Terminal access
-   Administrator / `sudo` access to your computer
-   Enough free disk space for PostgreSQL, Ollama, the required model,
    and the project

You do **not** need to manually install Python, PostgreSQL, Ollama,
Homebrew, or the Python packages before running the setup script.

------------------------------------------------------------------------

## 2. Open a Terminal

### macOS

Open **Terminal** from:

``` text
Applications → Utilities → Terminal
```

You can also use another shell such as iTerm2 if you already have it
configured.

### Linux

Open your distribution's terminal application
The setup script is intended to be run with Bash.

------------------------------------------------------------------------

## 3. Clone the Agent Harness Repository

Navigate to the directory where you want to store the project.

For example:

``` bash
cd ~/Desktop
```

Clone the repository:

``` bash
git clone https://github.com/Harsh-Sharma-2002/Agentic-harnesss
```

Replace `<REPOSITORY_URL>` with the GitHub repository URL provided for
the course. (https://github.com/Harsh-Sharma-2002/Agentic-harnesss)

Enter the repository:

``` bash
cd Agent_Harness
```

Verify your location:

``` bash
pwd
```

All remaining commands assume that you are inside the repository root
unless stated otherwise.

> The repository must be cloned before `setup.sh` can run because the
> setup script itself lives inside the repository.

------------------------------------------------------------------------

## 4. Make the Setup Script Executable

Run:

``` bash
chmod +x scripts/setup.sh
```

This gives the setup script permission to execute.

You normally only need to do this once.

------------------------------------------------------------------------

## 5. Run the Automated Setup

Run:

``` bash
./scripts/setup.sh
```

The script checks your machine and installs missing dependencies.

The setup process is approximately:

``` text
Detect macOS / Linux
      ↓
Install / verify system package tools
      ↓
Install / verify Git and curl
      ↓
Install / verify Python 3.11+
      ↓
Install / verify Ollama
      ↓
Install / verify PostgreSQL
      ↓
Start PostgreSQL le
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

Installation may take several minutes.

Do not close the terminal while setup is running.

The script is designed to be rerunnable. If setup is interrupted, you
can run it again.

------------------------------------------------------------------------

## 6. What Happens on macOS?

On macOS, the setup script uses **Homebrew** to install system
dependencies.

If Homebrew is not installed, the script installs it automatically.

Depending on your Homebrew is normally installed under one of
these locations:

``` text
/opt/homebrew
```

for Apple Silicon Macs, or:

``` text
/usr/local
```

for Intel Macs.

The script attempts to update the current shell environment after
Homebrew installation.

Homebrew is then used to install or verify:

-   Git
-   curl
-   Python
-   Ollama
-   PostgreSQL

You may be asked for your macOS password during system setup.

------------------------------------------------------------------------

## 7. What Happens on Linux?

On Linux, the setup script detects the available package manager.

Supported package managers include:

``` text
apt
dnf
yum
pacman
```

The script may use `sudo` to install system packages.

You may therefore be asked for your Linux user password.

Depending on the distribution, package names and PostgreSQL service
behavior may differ slightly. The script attempts to handle the common
supported distributions automatically.

------------------------------------------------------------------------

## 8. Restart the Terminal If Necessary

Some installations may update your shell environment or `PATH`.

If the setup script reports that Python, Ollama, PostgreSQL, or another
newly installed command cannot be found:

1.  Close the terminal.
2.  Open a new terminal.
3.  Return to the repository.
4.  Run setup again.

Example:

``` bash
cd ~/Desktop/Agent_Harness

./scripts/setup.sh
```

The setup script should detect and reuse dependencies that are already
installed.

------------------------------------------------------------------------

## 9. Activate the Python Virtual Environment

The setup script creates:

``` text
.venv
```

inside the repository.

Activate it with:

``` bash
source .venv/bin/activate
```

After activation, your terminal should look similar to:

``` text
(.venv) user@computer Agent_Harness %
```

or:

``` text
(.venv) user@computer:~/Agent_Harness$
```

The `(.venv)` prefix means the project environment is active.

Activate this environment whenever you open a new terminal for the
project.

------------------------------------------------------------------------

## 10. Verify Python

Run:

``` bash
python --version
```

The project requires **Python 3.11 or newer**.

Then verify `pip`:

``` bash
python -m pip --version
```

------------------------------------------------------------------------

## 11. Verify the Main Python Dependencies

Verify LangGraph:

``` bash
python -c "import langgraph; print('LangGraph OK')"
```

Expected output:

``` text
LangGraph OK
```

Verify LangChain:

``` bash
python -c "import langchain_core; print('LangChain OK')"
```

Verify FastAPI:

``` bash
python -c "import fastapi; print('FastAPI OK')"
```

Verify Streamlit:

``` bash
python -c "import streamlit; print('Streamlit OK')"
```

If these commands succeed, the main Python environment is configured
correctly.

------------------------------------------------------------------------

## 12. Verify Ollama

Run:

``` bash
ollama --version
```

You should see the installed Ollama version.

If `ollama` cannot be found immediately after installation, restart the
terminal and try again.

### macOS Note

The Ollama application may need to be opened once after installation
before the CLI/server is fully available.

You can open **Ollama** from the Applications folder if necessary.

------------------------------------------------------------------------

## 13. Start Ollama

Start the Ollama server:

``` bash
ollama serve
```

Keep this terminal open while using the Agent Harness.

By default, Ollama serves its local API at:

``` text
http://localhost:11434
```

If Ollama reports that the address is already in use, Ollama may already
be running.

Verify from another terminal with:

``` bash
ollama list
```

------------------------------------------------------------------------

## 14. Open a Second Terminal

Leave the Ollama server running.

Open another terminal and return to the repository:

``` bash
cd ~/Desktop/Agent_Harness
```

Activate the virtual environment:

``` bash
source .venv/bin/activate
```

Use this second terminal for the remaining project commands.

------------------------------------------------------------------------

## 15. Pull the Required Ollama Model

The setup script intentionally **does not download an Ollama model**.

Model downloads can require several gigabytes of disk space, so this
step is performed explicitly.

Pull the exact model specified for the course/project:

``` bash
ollama pull <MODEL_NAME>
```

Replace `<MODEL_NAME>` with the model specified by the instructor.

For example, if the course specifies `qwen3.5:4b`:

``` bash
ollama pull qwen3.5:4b
```

Wait for the model download to complete.

------------------------------------------------------------------------

## 16. Verify the Ollama Model

List installed models:

``` bash
ollama list
```

Confirm that the required model appears.

You can optionally test the model directly:

``` bash
ollama run <MODEL_NAME>
```

Enter a simple prompt such as:

``` text
Hello
```

Exit the interactive model session with:

``` text
/bye
```

------------------------------------------------------------------------

## 17. Configure `.env`

The setup script creates:

``` text
.env
```

from:

``` text
.env.example
```

when `.env.example` exists and `.env` does not already exist.

Open `.env` in your editor.

For VS Code:

``` bash
code .env
```

If the `code` command is unavailable, open `.env` manually in your
editor.

**Never commit `.env` to Git.**

The repository should keep `.env` in `.gitignore`.

------------------------------------------------------------------------

## 18. Configure Ollama in `.env`

Add or update:

``` dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=<MODEL_NAME>
```

Replace `<MODEL_NAME>` with the exact model you pulled.

Example:

``` dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
```

The model name must exactly match the value shown by:

``` bash
ollama list
```

------------------------------------------------------------------------

## 19. Configure LangSmith

LangSmith provides tracing and observability for LangGraph executions.

Add:

``` dotenv
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agent-harness
LANGSMITH_API_KEY=<YOUR_LANGSMITH_API_KEY>
```

Replace:

``` text
<YOUR_LANGSMITH_API_KEY>
```

with your own authorized LangSmith API key.

**Never commit or share your LangSmith API key.**

------------------------------------------------------------------------

## 20. Verify PostgreSQL

Run:

``` bash
psql --version
```

You should see the installed PostgreSQL version.

If `psql` is unavailable immediately after installation, restart the
terminal and try again.

------------------------------------------------------------------------

## 21. Verify PostgreSQL on macOS

If PostgreSQL was installed through Homebrew, check the service with:

``` bash
brew services list
```

Look for:

``` text
postgresql@17
```

The service should normally show:

``` text
started
```

If necessary:

``` bash
brew services start postgresql@17
```

------------------------------------------------------------------------

## 22. Verify PostgreSQL on Linux

On Linux systems using `systemd`, check:

``` bash
sudo systemctl status postgresql
```

If PostgreSQL is stopped:

``` bash
sudo systemctl start postgresql
```

To enable it at startup:

``` bash
sudo systemctl enable postgresql
```

If your Linux distribution does not use `systemd`, use the
service-management method provided by that distribution.

------------------------------------------------------------------------

## 23. Test PostgreSQL --- macOS

Homebrew PostgreSQL installations commonly use your current macOS
username as a local PostgreSQL role.

Try:

``` bash
psql postgres
```

If successful, you should see a PostgreSQL prompt similar to:

``` text
postgres=#
```

Exit with:

``` sql
\q
```

Depending on your PostgreSQL installation, authentication configuration
may differ.

------------------------------------------------------------------------

## 24. Test PostgreSQL --- Linux

Linux PostgreSQL installations commonly create a system user named:

``` text
postgres
```

Test the administrator connection with:

``` bash
sudo -u postgres psql
```

A successful connection should show:

``` text
postgres=#
```

Exit with:

``` sql
\q
```

------------------------------------------------------------------------

## 25. Project Database Credentials

The Agent Harness should **not** use the PostgreSQL administrator
account for normal Text2SQL execution.

Use a dedicated local project database account.

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

They are **not production credentials**.

The project database initialization process should create the matching
database and account.

------------------------------------------------------------------------

## 26. Why Use a Separate Database Account?

The PostgreSQL administrator has privileges that the Text2SQL agent does
not need.

The intended structure is:

``` text
PostgreSQL Administrator
        |
        +-- Agent Harness database
                |
                +-- Agent Harness account
                        |
                        +-- limited project permissions
```

This follows **least privilege**:

> Give each component only the permissions required to perform its job.

For Text2SQL, the runtime database account should eventually be limited
to the schemas, tables, and operations the agent actually requires.

------------------------------------------------------------------------

## 27. Final `.env` Shape

Your `.env` should eventually contain values similar to:

``` dotenv
# ==========================================================
# Ollama
# ==========================================================

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=<MODEL_NAME>


# ==========================================================
# LangSmith
# ==========================================================

LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agent-harness
LANGSMITH_API_KEY=<YOUR_LANGSMITH_API_KEY>


# ==========================================================
# PostgreSQL
# ==========================================================

DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=agent_harness
DATABASE_USER=agent_harness
DATABASE_PASSWORD=agent_harness_dev
```

Replace placeholders with the values specified for the course/project.

------------------------------------------------------------------------

## 28. Normal Startup on Future Sessions

After initial setup, you do **not** need to reinstall everything each
time.

### Terminal 1 --- Ollama

Start Ollama if it is not already running:

``` bash
ollama serve
```

Keep the terminal open.

### Terminal 2 --- Agent Harness

Navigate to the repository:

``` bash
cd <PATH_TO_AGENT_HARNESS>
```

Activate the virtual environment:

``` bash
source .venv/bin/activate
```

Then start the Agent Harness using the project's normal startup command.

------------------------------------------------------------------------

# Troubleshooting

## 29. Permission Denied When Running `setup.sh`

If:

``` bash
./scripts/setup.sh
```

returns a permission error, run:

``` bash
chmod +x scripts/setup.sh
```

Then retry:

``` bash
./scripts/setup.sh
```

------------------------------------------------------------------------

## 30. Command Not Found After Installation

If one of these commands is unavailable after setup:

``` text
git
python
ollama
psql
```

close the terminal and open a new terminal.

Then return to the repository:

``` bash
cd <PATH_TO_AGENT_HARNESS>
```

and rerun:

``` bash
./scripts/setup.sh
```

The script should detect software that is already installed.

------------------------------------------------------------------------

## 31. Ollama Is Not Responding

Check:

``` bash
ollama list
```

If necessary, start:

``` bash
ollama serve
```

The default endpoint is:

``` text
http://localhost:11434
```

Make sure `.env` contains:

``` dotenv
OLLAMA_BASE_URL=http://localhost:11434
```

------------------------------------------------------------------------

## 32. Ollama Model Not Found

List installed models:

``` bash
ollama list
```

If the required model is missing:

``` bash
ollama pull <MODEL_NAME>
```

Make sure `.env` contains the exact same name:

``` dotenv
OLLAMA_MODEL=<MODEL_NAME>
```

------------------------------------------------------------------------

## 33. PostgreSQL Connection Fails on macOS

Check Homebrew services:

``` bash
brew services list
```

If needed:

``` bash
brew services start postgresql@17
```

Then retry:

``` bash
psql postgres
```

If `psql` is not on `PATH`, restart the terminal and rerun setup.

------------------------------------------------------------------------

## 34. PostgreSQL Connection Fails on Linux

Check:

``` bash
sudo systemctl status postgresql
```

Start if necessary:

``` bash
sudo systemctl start postgresql
```

Test the administrator connection:

``` bash
sudo -u postgres psql
```

If the project-specific account later fails, verify:

``` text
DATABASE_HOST
DATABASE_PORT
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD
```

inside `.env`.

------------------------------------------------------------------------

## 35. Python Package Missing

Make sure the virtual environment is active.

Your prompt should begin with:

``` text
(.venv)
```

Then reinstall project dependencies:

``` bash
python -m pip install -r requirements.txt
```

Verify LangGraph:

``` bash
python -c "import langgraph; print('LangGraph OK')"
```

------------------------------------------------------------------------

## 36. `.env` Was Not Created

Check whether the repository contains:

``` text
.env.example
```

If it does:

``` bash
cp .env.example .env
```

Then edit `.env`.

------------------------------------------------------------------------

## 37. Virtual Environment Activation Fails

Confirm that `.venv` exists:

``` bash
ls -la .venv
```

If it does not exist, rerun:

``` bash
./scripts/setup.sh
```

If it exists, activate:

``` bash
source .venv/bin/activate
```

------------------------------------------------------------------------

## 38. Setup Was Interrupted

The setup script is designed to be rerunnable.

From the repository root:

``` bash
./scripts/setup.sh
```

The script should reuse already-installed dependencies, the existing
`.venv`, and the existing `.env`.

------------------------------------------------------------------------

# Security Notes

## 39. Never Commit `.env`

Verify `.gitignore` contains:

``` gitignore
.env
```

`.env` may contain API keys, database credentials, and local
configuration.

------------------------------------------------------------------------

## 40. Never Share API Keys

Do not publish:

``` text
LANGSMITH_API_KEY
```

If a key is accidentally exposed, revoke it and generate a new one.

------------------------------------------------------------------------

## 41. Do Not Run the Agent as PostgreSQL Administrator

The PostgreSQL administrator account is intended for administration.

Normal Text2SQL execution should use a dedicated project account with
limited permissions.

------------------------------------------------------------------------

# Final Setup Checklist

Before running the full Agent Harness, verify:

``` text
[ ] Repository cloned

[ ] setup.sh made executable

[ ] setup.sh completed

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

Once all required items are complete, the macOS/Linux environment is
ready for the Agent Harness.



 streamlit run ui/streamlit_app.py    
  uvicorn src.api.app:app --reload   
