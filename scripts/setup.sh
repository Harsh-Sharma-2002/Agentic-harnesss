#!/usr/bin/env bash

set -euo pipefail


# ==========================================================
# Agent Harness - Full Environment Setup
# macOS + Linux
#
# Installs:
#   - Git
#   - curl
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

section() {
    echo
    echo "=========================================================="
    echo " $1"
    echo "=========================================================="
    echo
}


ok() {
    echo "[OK] $1"
}


warn() {
    echo "[WARNING] $1"
}


fail() {
    echo
    echo "[ERROR] $1"
    echo
    exit 1
}


command_exists() {
    command -v "$1" >/dev/null 2>&1
}


# ==========================================================
# Start
# ==========================================================

section "Agent Harness Setup"


# ==========================================================
# Resolve Repository Root
# ==========================================================

SCRIPT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")" &&
    pwd
)"

REPO_ROOT="$(
    cd "$SCRIPT_DIR/.." &&
    pwd
)"

cd "$REPO_ROOT"

echo "Repository:"
echo "$REPO_ROOT"
echo


# ==========================================================
# Detect Platform
# ==========================================================

OS="$(uname -s)"

case "$OS" in

    Darwin)
        PLATFORM="macOS"
        ;;

    Linux)
        PLATFORM="Linux"
        ;;

    *)
        fail "Unsupported operating system: $OS"
        ;;

esac

ok "Detected $PLATFORM"


# ==========================================================
# Detect Linux Package Manager
# ==========================================================

PACKAGE_MANAGER=""

if [ "$PLATFORM" = "Linux" ]; then

    if command_exists apt-get; then
        PACKAGE_MANAGER="apt"

    elif command_exists dnf; then
        PACKAGE_MANAGER="dnf"

    elif command_exists yum; then
        PACKAGE_MANAGER="yum"

    elif command_exists pacman; then
        PACKAGE_MANAGER="pacman"

    else
        fail "No supported Linux package manager found."
    fi

    ok "Package manager: $PACKAGE_MANAGER"

fi


# ==========================================================
# Install Homebrew - macOS
# ==========================================================

if [ "$PLATFORM" = "macOS" ]; then

    section "Checking Homebrew"

    if command_exists brew; then

        ok "Homebrew already installed."

    else

        echo "Homebrew not found."
        echo "Installing Homebrew..."
        echo

        /bin/bash -c "$(
            curl -fsSL \
            https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh
        )"

        # Apple Silicon
        if [ -x "/opt/homebrew/bin/brew" ]; then

            eval "$(
                /opt/homebrew/bin/brew shellenv
            )"

        # Intel Mac
        elif [ -x "/usr/local/bin/brew" ]; then

            eval "$(
                /usr/local/bin/brew shellenv
            )"

        fi

        command_exists brew ||
            fail "Homebrew installation could not be verified."

        ok "Homebrew installed."

    fi

fi


# ==========================================================
# Install Base System Packages
# ==========================================================

section "Installing System Dependencies"

if [ "$PLATFORM" = "macOS" ]; then

    if ! command_exists git; then
        brew install git
    fi

    if ! command_exists curl; then
        brew install curl
    fi

elif [ "$PLATFORM" = "Linux" ]; then

    case "$PACKAGE_MANAGER" in

        apt)

            sudo apt-get update

            sudo apt-get install -y \
                git \
                curl \
                ca-certificates \
                build-essential

            ;;

        dnf)

            sudo dnf install -y \
                git \
                curl \
                ca-certificates \
                gcc \
                gcc-c++ \
                make

            ;;

        yum)

            sudo yum install -y \
                git \
                curl \
                ca-certificates \
                gcc \
                gcc-c++ \
                make

            ;;

        pacman)

            sudo pacman -Sy --needed --noconfirm \
                git \
                curl \
                ca-certificates \
                base-devel

            ;;

    esac

fi

command_exists git ||
    fail "Git installation failed."

command_exists curl ||
    fail "curl installation failed."

ok "Git available."
ok "curl available."


# ==========================================================
# Python
# ==========================================================

section "Checking Python"

PYTHON=""


# ----------------------------------------------------------
# Locate Existing Python
# ----------------------------------------------------------

if command_exists python3; then

    PYTHON="python3"

elif command_exists python; then

    PYTHON="python"

fi


# ----------------------------------------------------------
# Verify Existing Version
# ----------------------------------------------------------

if [ -n "$PYTHON" ]; then

    if "$PYTHON" - <<'PY'
import sys

raise SystemExit(
    0
    if sys.version_info >= (3, 11)
    else 1
)
PY
    then

        ok "Compatible Python already installed."

    else

        echo "Existing Python is older than 3.11."
        PYTHON=""

    fi

fi


# ----------------------------------------------------------
# Install Python if Required
# ----------------------------------------------------------

if [ -z "$PYTHON" ]; then

    echo "Installing Python..."
    echo

    if [ "$PLATFORM" = "macOS" ]; then

        brew install python

    else

        case "$PACKAGE_MANAGER" in

            apt)

                sudo apt-get install -y \
                    python3 \
                    python3-pip \
                    python3-venv \
                    python3-dev

                ;;

            dnf)

                sudo dnf install -y \
                    python3 \
                    python3-pip \
                    python3-devel

                ;;

            yum)

                sudo yum install -y \
                    python3 \
                    python3-pip \
                    python3-devel

                ;;

            pacman)

                sudo pacman -S --needed --noconfirm \
                    python \
                    python-pip

                ;;

        esac

    fi

    if command_exists python3; then
        PYTHON="python3"

    elif command_exists python; then
        PYTHON="python"

    else
        fail "Python installation failed."
    fi

fi


# ----------------------------------------------------------
# Final Python Check
# ----------------------------------------------------------

"$PYTHON" - <<'PY'
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
PY


# ==========================================================
# Ollama
# ==========================================================

section "Checking Ollama"

if command_exists ollama; then

    ok "Ollama already installed."

else

    echo "Installing Ollama..."
    echo

    if [ "$PLATFORM" = "macOS" ]; then

        brew install --cask ollama

    else

        curl -fsSL \
            https://ollama.com/install.sh |
            sh

    fi

fi


# ----------------------------------------------------------
# Refresh PATH / Verify
# ----------------------------------------------------------

if command_exists ollama; then

    ok "Ollama installed."

    ollama --version || true

else

    # On macOS the GUI app can exist before the CLI is
    # available to the current shell.
    if [ "$PLATFORM" = "macOS" ] &&
       [ -d "/Applications/Ollama.app" ]; then

        warn "Ollama application installed."
        warn "The CLI may become available after Ollama is opened once."

    else

        fail "Ollama installation could not be verified."

    fi

fi

echo
echo "No Ollama model is pulled by this script."


# ==========================================================
# PostgreSQL
# ==========================================================

section "Checking PostgreSQL"

if command_exists psql; then

    ok "PostgreSQL already installed."

else

    echo "Installing PostgreSQL..."
    echo

    if [ "$PLATFORM" = "macOS" ]; then

        brew install postgresql@17

    else

        case "$PACKAGE_MANAGER" in

            apt)

                sudo apt-get install -y \
                    postgresql \
                    postgresql-contrib \
                    libpq-dev

                ;;

            dnf)

                sudo dnf install -y \
                    postgresql \
                    postgresql-server \
                    postgresql-contrib \
                    libpq-devel

                ;;

            yum)

                sudo yum install -y \
                    postgresql \
                    postgresql-server \
                    postgresql-contrib \
                    postgresql-devel

                ;;

            pacman)

                sudo pacman -S --needed --noconfirm \
                    postgresql

                ;;

        esac

    fi

fi


# ==========================================================
# PostgreSQL PATH - macOS
# ==========================================================

if [ "$PLATFORM" = "macOS" ]; then

    if ! command_exists psql; then

        PG_PREFIX="$(
            brew --prefix postgresql@17 2>/dev/null ||
            true
        )"

        if [ -n "$PG_PREFIX" ] &&
           [ -d "$PG_PREFIX/bin" ]; then

            export PATH="$PG_PREFIX/bin:$PATH"

        fi

    fi

fi


command_exists psql ||
    fail "PostgreSQL installation could not be verified."

ok "PostgreSQL installed."

psql --version


# ==========================================================
# Start PostgreSQL
# ==========================================================

section "Starting PostgreSQL"

if [ "$PLATFORM" = "macOS" ]; then

    brew services start postgresql@17 \
        >/dev/null 2>&1 ||
        true

    ok "PostgreSQL service start requested."

else

    # ------------------------------------------------------
    # Initialize PostgreSQL when required on some distros
    # ------------------------------------------------------

    if [ "$PACKAGE_MANAGER" = "dnf" ] ||
       [ "$PACKAGE_MANAGER" = "yum" ]; then

        if [ -x "/usr/bin/postgresql-setup" ]; then

            sudo /usr/bin/postgresql-setup \
                --initdb \
                >/dev/null 2>&1 ||
                true

        fi

    fi


    # ------------------------------------------------------
    # systemd
    # ------------------------------------------------------

    if command_exists systemctl; then

        sudo systemctl enable postgresql \
            >/dev/null 2>&1 ||
            true

        sudo systemctl start postgresql \
            >/dev/null 2>&1 ||
            true

        ok "PostgreSQL service start requested."

    else

        warn "systemctl not available."
        warn "PostgreSQL may need to be started manually."

    fi

fi


# ==========================================================
# Virtual Environment
# ==========================================================

section "Creating Python Environment"

VENV_DIR="$REPO_ROOT/.venv"

if [ -d "$VENV_DIR" ]; then

    ok "Virtual environment already exists."

else

    "$PYTHON" -m venv "$VENV_DIR"

    ok "Virtual environment created."

fi


# ----------------------------------------------------------
# Activate
# ----------------------------------------------------------

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

ok "Virtual environment activated."

echo
echo "Virtual environment Python:"
python --version


# ==========================================================
# Python Packaging Tools
# ==========================================================

section "Updating Python Packaging Tools"

python -m pip install \
    --upgrade \
    pip \
    setuptools \
    wheel

ok "pip, setuptools and wheel updated."


# ==========================================================
# Project Requirements
# ==========================================================

section "Installing Project Dependencies"

REQUIREMENTS="$REPO_ROOT/requirements.txt"

[ -f "$REQUIREMENTS" ] ||
    fail "requirements.txt was not found."

python -m pip install \
    -r "$REQUIREMENTS"

ok "requirements.txt installed."


# ==========================================================
# Environment File
# ==========================================================

section "Configuring Environment File"

ENV_FILE="$REPO_ROOT/.env"
ENV_EXAMPLE="$REPO_ROOT/.env.example"

if [ -f "$ENV_FILE" ]; then

    ok ".env already exists."

elif [ -f "$ENV_EXAMPLE" ]; then

    cp "$ENV_EXAMPLE" "$ENV_FILE"

    ok ".env created from .env.example."

else

    warn ".env.example was not found."
    warn "No .env file was created."

fi


# ==========================================================
# Verify Python Dependencies
# ==========================================================

section "Verifying Python Dependencies"

python - <<'PY'
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
PY


# ==========================================================
# Verify External Dependencies
# ==========================================================

section "Verifying External Dependencies"


# ----------------------------------------------------------
# Git
# ----------------------------------------------------------

git --version

ok "Git verified."


# ----------------------------------------------------------
# Ollama
# ----------------------------------------------------------

if command_exists ollama; then

    ollama --version || true

    ok "Ollama verified."

else

    warn "Ollama CLI is not currently on PATH."

fi


# ----------------------------------------------------------
# PostgreSQL
# ----------------------------------------------------------

psql --version

ok "PostgreSQL verified."


# ==========================================================
# Final Summary
# ==========================================================

section "Setup Complete"

echo "The Agent Harness development environment is ready."
echo

echo "Installed / configured:"
echo
echo "  [OK] Git"
echo "  [OK] curl"
echo "  [OK] Python 3.11+"
echo "  [OK] Python virtual environment"
echo "  [OK] Python project dependencies"
echo "  [OK] Ollama"
echo "  [OK] PostgreSQL"
echo

if [ -f "$ENV_FILE" ]; then

    echo "Environment configuration:"
    echo
    echo "  $ENV_FILE"
    echo

fi

echo "Virtual environment:"
echo
echo "  $VENV_DIR"
echo

echo "To activate the environment later:"
echo
echo "  source .venv/bin/activate"
echo

echo "Important:"
echo
echo "  This setup intentionally does NOT pull an Ollama model."
echo "  The required model and remaining project configuration"
echo "  will be covered in the project setup instructions."
echo