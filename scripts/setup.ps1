#Requires -Version 5.1

$ErrorActionPreference = "Stop"


# ==========================================================
# Agent Harness - Full Environment Setup
# Windows PowerShell
#
# Installs:
#   - Git
#   - Python 3.11+
#   - Python virtual environment
#   - Project Python dependencies
#   - Ollama
#   - PostgreSQL
#
# Does NOT:
#   - Pull an Ollama model
#   - Configure LangSmith credentials
#   - Populate project-specific database data
# ==========================================================


# ==========================================================
# Formatting Helpers
# ==========================================================

function Write-Section {

    param(
        [string]$Title
    )

    Write-Host ""
    Write-Host "=========================================================="
    Write-Host " $Title"
    Write-Host "=========================================================="
    Write-Host ""

}


function Write-OK {

    param(
        [string]$Message
    )

    Write-Host "[OK] $Message"

}


function Write-WarningMessage {

    param(
        [string]$Message
    )

    Write-Host "[WARNING] $Message" -ForegroundColor Yellow

}


function Stop-Setup {

    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    Write-Host ""

    exit 1

}


function Test-Command {

    param(
        [string]$Command
    )

    return [bool](
        Get-Command `
            $Command `
            -ErrorAction SilentlyContinue
    )

}


# ==========================================================
# Start
# ==========================================================

Write-Section "Agent Harness Setup"


# ==========================================================
# Resolve Repository Root
# ==========================================================

$ScriptDir = Split-Path `
    -Parent `
    $MyInvocation.MyCommand.Path

$RepoRoot = Resolve-Path (
    Join-Path `
        $ScriptDir `
        ".."
)

Set-Location $RepoRoot

Write-Host "Repository:"
Write-Host $RepoRoot
Write-Host ""

Write-OK "Detected Windows"


# ==========================================================
# Check winget
# ==========================================================

Write-Section "Checking Windows Package Manager"

if (-not (Test-Command "winget")) {

    Stop-Setup @"
winget was not found.

winget is included with Microsoft App Installer on modern
Windows 10 and Windows 11 installations.

Install/update App Installer from the Microsoft Store,
then run this setup script again.
"@

}

Write-OK "winget available."


# ==========================================================
# Refresh PATH Helper
# ==========================================================

function Update-ProcessPath {

    $MachinePath = (
        [Environment]::GetEnvironmentVariable(
            "Path",
            "Machine"
        )
    )

    $UserPath = (
        [Environment]::GetEnvironmentVariable(
            "Path",
            "User"
        )
    )

    $env:Path = (
        $MachinePath +
        ";" +
        $UserPath
    )

}


# ==========================================================
# Git
# ==========================================================

Write-Section "Checking Git"

if (Test-Command "git") {

    Write-OK "Git already installed."

}
else {

    Write-Host "Installing Git..."
    Write-Host ""

    winget install `
        --id Git.Git `
        --exact `
        --accept-package-agreements `
        --accept-source-agreements `
        --silent

    Update-ProcessPath

}

if (-not (Test-Command "git")) {

    Stop-Setup "Git installation could not be verified."

}

git --version

Write-OK "Git verified."


# ==========================================================
# Python
# ==========================================================

Write-Section "Checking Python"

$Python = $null


# ----------------------------------------------------------
# Find Existing Python
# ----------------------------------------------------------

if (Test-Command "python") {

    $Python = "python"

}
elseif (Test-Command "py") {

    $Python = "py"

}


# ----------------------------------------------------------
# Verify Existing Version
# ----------------------------------------------------------

$PythonCompatible = $false

if ($null -ne $Python) {

    $VersionScript = @"
import sys

raise SystemExit(
    0
    if sys.version_info >= (3, 11)
    else 1
)
"@

    $VersionScript | & $Python -

    if ($LASTEXITCODE -eq 0) {

        $PythonCompatible = $true

        Write-OK "Compatible Python already installed."

    }
    else {

        Write-Host "Existing Python is older than 3.11."

        $Python = $null

    }

}


# ----------------------------------------------------------
# Install Python
# ----------------------------------------------------------

if (-not $PythonCompatible) {

    Write-Host "Installing Python 3.12..."
    Write-Host ""

    winget install `
        --id Python.Python.3.12 `
        --exact `
        --accept-package-agreements `
        --accept-source-agreements `
        --silent

    Update-ProcessPath


    if (Test-Command "python") {

        $Python = "python"

    }
    elseif (Test-Command "py") {

        $Python = "py"

    }
    else {

        Stop-Setup @"
Python was installed but is not available in the current
PowerShell session.

Close this terminal, open PowerShell again, and rerun:

    .\scripts\setup.ps1
"@

    }

}


# ----------------------------------------------------------
# Final Python Version Check
# ----------------------------------------------------------

$PythonVersionCheck = @"
import sys

minimum = (3, 11)

if sys.version_info < minimum:

    print(
        "[ERROR] Python 3.11 or newer is required."
    )

    print(
        "Detected:",
        sys.version,
    )

    raise SystemExit(1)

print(
    "[OK] Python:",
    sys.version.split()[0],
)
"@

$PythonVersionCheck | & $Python -

if ($LASTEXITCODE -ne 0) {

    Stop-Setup "Python version check failed."

}


# ==========================================================
# Ollama
# ==========================================================

Write-Section "Checking Ollama"

if (Test-Command "ollama") {

    Write-OK "Ollama already installed."

}
else {

    Write-Host "Installing Ollama..."
    Write-Host ""

    winget install `
        --id Ollama.Ollama `
        --exact `
        --accept-package-agreements `
        --accept-source-agreements `
        --silent

    Update-ProcessPath

}


# ----------------------------------------------------------
# Verify Ollama
# ----------------------------------------------------------

if (Test-Command "ollama") {

    ollama --version

    Write-OK "Ollama verified."

}
else {

    Write-WarningMessage @"
Ollama was installed but its CLI is not currently available.

This can happen because Windows has not refreshed the PATH
for the current PowerShell session.

You may need to close and reopen PowerShell after setup.
"@

}

Write-Host ""
Write-Host "No Ollama model is pulled by this script."


# ==========================================================
# PostgreSQL
# ==========================================================

Write-Section "Checking PostgreSQL"

if (Test-Command "psql") {

    Write-OK "PostgreSQL already installed."

}
else {

    Write-Host "Installing PostgreSQL..."
    Write-Host ""

    # ------------------------------------------------------
    # Install PostgreSQL
    #
    # PostgreSQL's Windows installer may require additional
    # setup depending on the version provided by winget.
    # ------------------------------------------------------

    winget install `
        --id PostgreSQL.PostgreSQL `
        --exact `
        --accept-package-agreements `
        --accept-source-agreements `
        --silent

    Update-ProcessPath

}


# ==========================================================
# Locate PostgreSQL CLI
# ==========================================================

if (-not (Test-Command "psql")) {

    $PostgresRoot = "C:\Program Files\PostgreSQL"

    if (Test-Path $PostgresRoot) {

        $PostgresVersions = (
            Get-ChildItem `
                $PostgresRoot `
                -Directory `
                -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending
        )

        foreach ($Version in $PostgresVersions) {

            $BinPath = Join-Path `
                $Version.FullName `
                "bin"

            $PsqlPath = Join-Path `
                $BinPath `
                "psql.exe"

            if (Test-Path $PsqlPath) {

                $env:Path = (
                    $BinPath +
                    ";" +
                    $env:Path
                )

                break

            }

        }

    }

}


# ----------------------------------------------------------
# Verify PostgreSQL
# ----------------------------------------------------------

if (Test-Command "psql") {

    psql --version

    Write-OK "PostgreSQL verified."

}
else {

    Write-WarningMessage @"
PostgreSQL appears to have been installed, but psql is not
currently available on PATH.

You may need to close and reopen PowerShell after setup.
"@

}


# ==========================================================
# Check PostgreSQL Windows Service
# ==========================================================

Write-Section "Checking PostgreSQL Service"

$PostgresService = (
    Get-Service `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -like "postgresql*"
    } |
    Select-Object -First 1
)

if ($null -ne $PostgresService) {

    if ($PostgresService.Status -ne "Running") {

        Write-Host "Starting PostgreSQL service..."

        try {

            Start-Service `
                $PostgresService.Name

            Write-OK "PostgreSQL service started."

        }
        catch {

            Write-WarningMessage @"
PostgreSQL is installed, but the setup script could not
start the Windows service automatically.

The service may require administrator privileges.
"@

        }

    }
    else {

        Write-OK "PostgreSQL service already running."

    }

}
else {

    Write-WarningMessage @"
No PostgreSQL Windows service was detected.

The PostgreSQL installer may require a terminal restart
before the service becomes visible.
"@

}


# ==========================================================
# Python Virtual Environment
# ==========================================================

Write-Section "Creating Python Environment"

$VenvDir = Join-Path `
    $RepoRoot `
    ".venv"

if (Test-Path $VenvDir) {

    Write-OK "Virtual environment already exists."

}
else {

    Write-Host "Creating virtual environment..."

    & $Python `
        -m `
        venv `
        $VenvDir

    if ($LASTEXITCODE -ne 0) {

        Stop-Setup "Virtual environment creation failed."

    }

    Write-OK "Virtual environment created."

}


# ==========================================================
# Virtual Environment Python
# ==========================================================

$VenvPython = Join-Path `
    $VenvDir `
    "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {

    Stop-Setup @"
The virtual environment exists, but its Python executable
could not be found:

$VenvPython
"@

}

Write-OK "Virtual environment ready."

Write-Host ""
Write-Host "Virtual environment Python:"

& $VenvPython --version


# ==========================================================
# Upgrade Python Packaging Tools
# ==========================================================

Write-Section "Updating Python Packaging Tools"

& $VenvPython `
    -m `
    pip `
    install `
    --upgrade `
    pip `
    setuptools `
    wheel

if ($LASTEXITCODE -ne 0) {

    Stop-Setup "Failed to upgrade Python packaging tools."

}

Write-OK "pip, setuptools and wheel updated."


# ==========================================================
# Install Project Requirements
# ==========================================================

Write-Section "Installing Project Dependencies"

$Requirements = Join-Path `
    $RepoRoot `
    "requirements.txt"

if (-not (Test-Path $Requirements)) {

    Stop-Setup @"
requirements.txt was not found:

$Requirements
"@

}

& $VenvPython `
    -m `
    pip `
    install `
    -r `
    $Requirements

if ($LASTEXITCODE -ne 0) {

    Stop-Setup "Failed to install requirements.txt."

}

Write-OK "requirements.txt installed."


# ==========================================================
# Environment File
# ==========================================================

Write-Section "Configuring Environment File"

$EnvFile = Join-Path `
    $RepoRoot `
    ".env"

$EnvExample = Join-Path `
    $RepoRoot `
    ".env.example"

if (Test-Path $EnvFile) {

    Write-OK ".env already exists."

}
elseif (Test-Path $EnvExample) {

    Copy-Item `
        $EnvExample `
        $EnvFile

    Write-OK ".env created from .env.example."

}
else {

    Write-WarningMessage @"
.env.example was not found.

No .env file was created.
"@

}


# ==========================================================
# Verify Core Python Dependencies
# ==========================================================

Write-Section "Verifying Python Dependencies"

$ImportCheck = @"
modules = {
    "fastapi": "FastAPI",
    "langchain_core": "LangChain",
    "langgraph": "LangGraph",
    "pydantic": "Pydantic",
    "streamlit": "Streamlit",
}

failed = []

for module, display_name in modules.items():

    try:

        __import__(module)

        print(
            f"[OK] {display_name}"
        )

    except ImportError:

        print(
            f"[ERROR] {display_name}"
        )

        failed.append(
            display_name
        )


if failed:

    print()

    print(
        "Missing Python dependencies:",
        ", ".join(failed),
    )

    raise SystemExit(1)
"@

$ImportCheck | & $VenvPython -

if ($LASTEXITCODE -ne 0) {

    Stop-Setup "Python dependency verification failed."

}


# ==========================================================
# External Dependency Summary
# ==========================================================

Write-Section "Verifying External Dependencies"


# ----------------------------------------------------------
# Git
# ----------------------------------------------------------

if (Test-Command "git") {

    git --version

    Write-OK "Git verified."

}
else {

    Write-WarningMessage "Git is not currently available on PATH."

}


# ----------------------------------------------------------
# Ollama
# ----------------------------------------------------------

if (Test-Command "ollama") {

    ollama --version

    Write-OK "Ollama verified."

}
else {

    Write-WarningMessage @"
Ollama is installed but not currently available on PATH.

Restart PowerShell before continuing.
"@

}


# ----------------------------------------------------------
# PostgreSQL
# ----------------------------------------------------------

if (Test-Command "psql") {

    psql --version

    Write-OK "PostgreSQL verified."

}
else {

    Write-WarningMessage @"
PostgreSQL is installed but psql is not currently available
on PATH.

Restart PowerShell before continuing.
"@

}


# ==========================================================
# Setup Complete
# ==========================================================

Write-Section "Setup Complete"

Write-Host "The Agent Harness development environment is ready."
Write-Host ""

Write-Host "Installed / configured:"
Write-Host ""

Write-Host "  [OK] Git"
Write-Host "  [OK] Python 3.11+"
Write-Host "  [OK] Python virtual environment"
Write-Host "  [OK] Python project dependencies"
Write-Host "  [OK] Ollama"
Write-Host "  [OK] PostgreSQL"

Write-Host ""

if (Test-Path $EnvFile) {

    Write-Host "Environment configuration:"
    Write-Host ""
    Write-Host "  $EnvFile"
    Write-Host ""

}

Write-Host "Virtual environment:"
Write-Host ""
Write-Host "  $VenvDir"
Write-Host ""

Write-Host "To activate the environment later:"
Write-Host ""
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""

Write-Host "Important:"
Write-Host ""
Write-Host "  This setup intentionally does NOT pull an Ollama model."
Write-Host "  The required model and remaining project configuration"
Write-Host "  will be covered in the project setup instructions."
Write-Host ""