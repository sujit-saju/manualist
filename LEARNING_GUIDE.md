# Building Manualist step by step

Use [Project_Specs.md](Project_Specs.md) for product requirements and engineering standards. Use this guide for the order of the lessons and the current checkpoint. The project folders are `Server/` and `UI/`, which correspond to `backend/` and `frontend/` in the spec.

## Server layout

You’ll create the folder structure under `Server/src/`. Organize code by responsibility first, then by feature within each responsibility. Keep API modules for routing and request handling, service modules for business logic, and repository modules for database access. For example, document routes belong in the API layer, and document business rules belong in the corresponding service module. We’ll use the package names and paths you create when updating imports, packaging, and tests.

## Development environment

Use Ubuntu on WSL 2 with Docker Desktop's WSL integration for the full stack. You can keep VS Code and your browser on Windows. When running Linux tools regularly, keep the working checkout under a Linux path such as `~/projects/Manualist` for faster file access and reliable Docker file watching. The current files are still on `D:`. Keep using that copy for the first exercise if you already have Windows Python 3.12 and uv. [Microsoft WSL setup](https://learn.microsoft.com/en-us/windows/wsl/setup/environment) · [Docker WSL best practices](https://docs.docker.com/desktop/features/wsl/best-practices)

From PowerShell, `wsl --list --verbose` shows installed distributions and their WSL versions. In whichever shell you use for development, run `uv --version` to check that uv is available.

## How we work through a lesson

1. Read the relevant spec section and identify what should happen from the caller's perspective.
2. Make one small change and explain the new concept before introducing the next one.
3. Run a focused check, inspect the output, and try a small exercise.
4. Record the result here. Verify unfamiliar APIs against installed source or official docs. Record unresolved spec details in [Docs/OPEN_QUESTIONS.md](Docs/OPEN_QUESTIONS.md) and deviations in [Docs/DECISIONS.md](Docs/DECISIONS.md).

## M0, lesson 1 · FastAPI app factory and liveness

**Status:** The health test passed in the user's WSL environment.

- `pyproject.toml` declares Python 3.12, FastAPI, and the tools used in this lesson.
- `create_app()` constructs the FastAPI app and registers the health router. A router groups related endpoints. Separating it from the factory gives tests and the command-line server the same entry point.
- Liveness answers whether the API process can serve a request. Readiness will check external dependencies in a later lesson.
- The test sends an HTTP request directly to the ASGI app through HTTPX. This exercises routing and serialization without starting a listening server.

From `Server/`, run:

```sh
uv sync
uv run pytest
uv run uvicorn src.main:create_app --factory --reload
```

If you’re using an activated Python 3.12 virtual environment with pip, run these commands from `Server/`:

```sh
python -m pip install -r requirements.txt
python -m pytest
python -m uvicorn src.main:create_app --factory --reload
```

`-e .` installs the local `manualist` distribution, which exposes the `src` import package, and pulls its runtime dependencies from `pyproject.toml`. Editable installation lets the interpreter see your source edits without reinstalling the package.

With Uvicorn running, open `http://127.0.0.1:8000/api/v1/health/live` and expect HTTP 200 with `{"status":"ok"}`. As an exercise, predict what happens if you request `/health/live` without the `/api/v1` prefix, then try it in the browser.

## M0, lesson 2 · Typed settings

**Status:** Verified on WSL. The async fixture loop scope is now explicit in `pyproject.toml`.

`Server/src/core/config.py` reads `APP_ENV` when the app starts. The `Literal` type allows `development`, `test`, or `production`. A typo such as `prodution` fails validation instead of silently enabling the API docs. FastAPI uses `openapi_url=None` in production to omit the OpenAPI schema and both documentation pages.

From `Server/`, with your virtual environment active, reinstall the local project to pick up `pydantic-settings`, then run the tests:

```sh
python -m pip install -r requirements.txt
python -m pytest
```

In WSL, try `APP_ENV=production python -m uvicorn src.main:create_app --factory`. Predict what `/docs` and `/api/v1/health/live` return before opening them.

## M0 handoff

You added request IDs, matched one to a JSON log, and tested the readiness route with a fake check. The scaffold now has real probes for PostgreSQL, Redis, and Ollama. The [README](README.md) covers running the full stack and [the architecture notes](Docs/ARCHITECTURE.md) show where the pieces live.

The local test suite runs without Ollama model downloads. In Compose, liveness works while readiness reports `models_missing` until you pull the configured model tags. Your current ignored `.env` uses port 18000 for Compose so it can coexist with the Uvicorn server on port 8000.

## M1 practice · Registration

Start with the register endpoint contract in Sections 4, 7, and 10 of the spec. Work through the request and response schemas, user migration, password hashing, and registration service in small steps. Then verify the HTTP response and duplicate-email behavior before starting login. You write the implementation and we review each step together.
