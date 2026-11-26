# Decision records

## ADR-001: Package the server with Hatchling and serve it with Uvicorn

- Date: 2026-11-24
- Status: accepted
- Context: The spec requires a `src/` layout and uv, and leaves the Python build backend and ASGI server unspecified.
- Decision: Use Hatchling to install the `manualist` package and Uvicorn to run its FastAPI app factory locally.
- Consequences: The editable distribution exposes the `src` import package. Tests and Uvicorn use `src.main` without setting `PYTHONPATH`.

## ADR-002: Use the existing Manualist folder layout

- Date: 2026-11-25
- Status: accepted
- Context: The user organized the workspace as `Server/src/` and `UI/`, with backend modules grouped by responsibility.
- Decision: Use `Server/`, `UI/`, and the existing `Docs/` for tooling and documentation. Use `src` as the server import package.
- Consequences: Paths in the spec map to the existing directories, and feature modules can be added without moving the scaffold.

## ADR-003: Bootstrap Docker and UI tooling

- Date: 2026-11-25
- Status: accepted
- Context: M0 requires an async PostgreSQL connection, a Redis health probe, frontend build tooling, and a web container.
- Decision: Use asyncpg with SQLAlchemy, redis-py, the Tailwind Vite plugin, jsdom for UI tests, pytest-cov and Vitest V8 for coverage, and Nginx for the static Compose UI.
- Consequences: ASGI and UI tests run locally. Compose hosts built UI files, while the Vite dev server remains available for frontend work.

## ADR-004: Build the MinIO development image from upstream source

- Date: 2026-11-25
- Status: accepted
- Context: Anonymous pulls of the published community MinIO images failed on both Docker Hub and Quay.
- Decision: Build the development container from the official MinIO security release tag.
- Consequences: The first Compose build compiles MinIO. Subsequent builds reuse the resulting image layers.
