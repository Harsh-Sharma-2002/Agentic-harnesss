# Agent Harness --- Docker Setup Guide

This is the primary setup path for running the **Agent Harness**. It requires only Git and Docker — no local Python, PostgreSQL, or Ollama installation.

## 1. Clone the repository

```bash
git clone https://github.com/Harsh-Sharma-2002/Agentic-harnesss.git
cd Agentic-harnesss
```

## 2. Run the stack

```bash
docker compose up --build
```

This builds the API/UI images and starts PostgreSQL, Ollama, and the application containers.

## 3. Wait for the model pull

On first run, the `ollama-init` container pulls the configured LLM model before the API starts. This can take several minutes depending on your connection — subsequent runs reuse the cached model and start much faster.

## 4. Open the app

- UI: [http://localhost:8501](http://localhost:8501)
- API health check: [http://localhost:8000/health](http://localhost:8000/health)

## 5. Stop and reset

```bash
docker compose down -v
```

This stops all containers and removes their volumes (including the downloaded model and database data), giving you a clean slate for the next run.

---

Looking to run the harness without Docker instead? See [ADVANCED_LOCAL_SETUP.md](ADVANCED_LOCAL_SETUP.md) (macOS/Linux) or [WINDOWS_LOCAL_SETUP.md](WINDOWS_LOCAL_SETUP.md) (Windows).
