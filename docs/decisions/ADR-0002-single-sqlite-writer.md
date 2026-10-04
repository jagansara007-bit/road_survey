# ADR-0002: Single SQLite Writer

**Status:** Proposed

## Context

The Road Damage Detection system uses SQLite as its persistence layer. SQLite supports concurrent reads but only one writer at a time. In a web-service context, concurrent write attempts can cause `SQLITE_BUSY` errors and data corruption if not handled carefully.

## Decision

1. **Single writer process.** The FastAPI service runs as a single process. All database writes happen through one connection managed by the application. Background tasks (e.g., video processing) share this writer through dependency injection.

2. **WAL mode.** The database is opened with `PRAGMA journal_mode=WAL`, which allows concurrent readers while a write transaction is in progress. This is critical for serving `GET` requests while a survey is being processed.

3. **Foreign keys enforced.** Every connection executes `PRAGMA foreign_keys=ON` immediately after opening.

4. **All SQL lives in `app/db/`.** No other module may import `sqlite3` or construct SQL strings. Repository classes provide the sole interface to persistent storage.

5. **Parameterised queries only.** All queries use `?` placeholders. String concatenation or f-strings to build SQL are explicitly forbidden and checked by a lint test.

## Consequences

- The system cannot scale horizontally with multiple writer processes against the same SQLite file. This is acceptable for the project scope (single-server deployment, demo use case).
- If horizontal scaling is ever needed, the repository interface is narrow enough to swap SQLite for PostgreSQL without changing callers.
- WAL mode increases disk usage slightly (WAL file + shared-memory file) but this is negligible for the expected data volumes.
