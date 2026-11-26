# Open questions

- **M3 retrieval budget:** Section 6.1 gives `MAX_CONTEXT_TOKENS` a default of 6,000. Section 12 gives 4,500. Confirm the default when implementing retrieval.

## Resolved

- **M0 readiness:** Combine Sections 2.3 and 7.2. Readiness requires PostgreSQL, Redis, and pre-pulled Ollama models. Liveness and the default test suite work without those models.
