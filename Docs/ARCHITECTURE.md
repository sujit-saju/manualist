# Manualist architecture

## M0 request flow

The browser UI checks the versioned liveness endpoint using TanStack Query. Its route type comes from the checked-in FastAPI OpenAPI schema. Configure the allowed UI origins through `CORS_ALLOWED_ORIGINS`.

The FastAPI app factory loads typed environment settings and installs request middleware once. The middleware accepts a bounded request ID from the caller or generates one, stores it on the request, and adds it to the response and JSON request log. It records the method, path, response code, and elapsed time.

- `GET /api/v1/health/live` reports whether the API can serve HTTP requests.
- `GET /api/v1/health/ready` runs concurrent, time-bounded probes. PostgreSQL executes `SELECT 1`, Redis responds to `PING`, and Ollama lists local tags for the configured models. Missing settings, connection failures, and missing Ollama models produce a 503 response with dependency status.
- Compose builds the API, Celery worker, and static web UI. PostgreSQL, Redis, MinIO, and Ollama run alongside them. The Celery worker connects to Redis. Ingestion tasks arrive in M2.

## Source layout

`Server/src/` is the Python import package. API routes live in `api/v1/`, shared configuration and middleware in `core/`, and dependency checks in `services/`. `UI/src/` contains the React app, API client code, and global styles. Authentication starts with its own API and service modules in M1.
