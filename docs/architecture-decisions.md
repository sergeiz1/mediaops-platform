# Architecture Decisions

## ADR-001: FastAPI as Primary Backend Framework

### Decision

Use FastAPI for the main API service.

### Context

The platform needs:

- typed request/response contracts
- fast iteration speed
- clear API docs for demo and integration

### Consequences

- Strong developer ergonomics with Pydantic and type hints
- OpenAPI docs out of the box
- Async-friendly ecosystem

---

## ADR-002: PostgreSQL as Source of Truth

### Decision

Use PostgreSQL for canonical persistence of assets and metadata.

### Context

Assets, statuses, and lifecycle metadata need consistency and transactional updates.

### Consequences

- Reliable transactional model for CRUD and status changes
- Structured migration path with Alembic
- Enables deterministic reindex to OpenSearch

---

## ADR-003: Celery + Redis for Background Processing

### Decision

Use Celery workers with Redis as broker/result backend.

### Context

Media processing is asynchronous and should not block API requests.

### Consequences

- Non-blocking processing flow (`uploaded -> processing -> ready/failed`)
- Worker scaling path exists
- Windows local dev requires `--pool=solo`

---

## ADR-004: OpenSearch for Search and Discovery

### Decision

Use OpenSearch for search/filter queries, with PostgreSQL fallback.

### Context

Search UX requires fast full-text matching and flexible filtering.

### Consequences

- Better search relevance and scalability path
- Need index sync on create/update/delete/status changes
- Added reindex endpoint for drift recovery

---

## ADR-005: Local File Storage as MVP Upload Target

### Decision

Store uploaded files in local `storage/uploads` for MVP.

### Context

A lightweight upload flow is needed before introducing object-storage complexity.

### Consequences

- Fast local iteration
- Simplified developer setup
- Clear migration path to MinIO/S3 via `file_key` abstraction

---

## Migration Strategy

1. Keep PostgreSQL as canonical source.
2. Route reads through OpenSearch when available.
3. Keep fallback path to PostgreSQL search if OpenSearch is down.
4. Use `/api/v1/assets/reindex` to rebuild index from canonical DB.

## Rollback Strategy

- If OpenSearch fails:
  - set `OPENSEARCH_ENABLED=false`
  - continue serving search through PostgreSQL filters
- If migration fails:
  - use Alembic downgrade where safe
  - restore from DB backup when needed

## Integration Boundaries

- API owns business workflows and validation.
- Worker owns asynchronous processing transitions.
- Search service owns indexing/reindexing mechanics.
- Repository layer owns DB query construction.
