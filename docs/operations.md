# Operations Runbook

## 1. Scope

Dieses Runbook beschreibt den operativen Betrieb der MediaOps Platform in der lokalen/preview-nahen Umgebung:

- `frontend` (Vite/React)
- `backend` (FastAPI)
- `worker` (Celery)
- `postgres`
- `redis`
- `opensearch`

## 2. Startup Sequence

1. Infrastruktur starten:

```bash
docker compose up -d postgres redis opensearch
```

2. Backend-Migrationen:

```bash
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

3. API starten:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Worker starten (Windows):

```bash
cd backend
.\run_worker.ps1
```

5. Frontend starten:

```bash
cd frontend
npm run dev
```

## 3. Health and Readiness Checks

### API

- Health endpoint: `GET /api/v1/health`
- Erwartung: `{"status":"ok"}`

### PostgreSQL

- Containerstatus: `docker compose ps`
- Erwartung: `mediaops-postgres` = `healthy`

### Redis

- Containerstatus: `docker compose ps`
- Erwartung: `mediaops-redis` = `healthy`

### OpenSearch

- Endpoint: `http://localhost:9200`
- Erwartung: JSON mit `cluster_name`/`version`

### Celery

- Worker-Logs prüfen
- Erwartung: Task `asset.process` ist registriert, keine reconnect loop

## 4. Typical Runtime Tasks

### Seed-Daten einspielen

```bash
cd backend
.\.venv\Scripts\python.exe -m scripts.seed_cern_assets
```

### OpenSearch reindex

```bash
curl -X POST http://localhost:8000/api/v1/assets/reindex
```

### Asset-Processing anstoßen

```bash
curl -X POST http://localhost:8000/api/v1/assets/{id}/process
```

## 5. Incident Playbook

### Symptom: `500` auf `/api/v1/assets`

Check:

1. `DATABASE_URL` im Backend-Process prüfen
2. `docker compose ps` auf `postgres` Status prüfen
3. API-Logs auf `OperationalError` analysieren

### Symptom: Reindex liefert `indexed: 0`

Check:

1. Ist OpenSearch unter `localhost:9200` erreichbar?
2. Ist `OPENSEARCH_ENABLED=true` gesetzt?
3. Gibt es Daten in PostgreSQL?

### Symptom: Celery verarbeitet nicht

Check:

1. Läuft Redis?
2. Läuft Worker mit korrekter App-Referenz?
3. Unter Windows `--pool=solo` verwenden

## 6. Logs and Debugging

### Docker logs

```bash
docker compose logs postgres --tail=100
docker compose logs redis --tail=100
docker compose logs opensearch --tail=100
```

### App logs

- Uvicorn-Output direkt im API-Terminal
- Celery-Output direkt im Worker-Terminal

## 7. Backup and Recovery (Minimum Baseline)

### PostgreSQL dump

```bash
docker exec -e PGPASSWORD=postgres -i mediaops-postgres pg_dump -U postgres -d mediaops > mediaops_dump.sql
```

### Restore

```bash
docker exec -e PGPASSWORD=postgres -i mediaops-postgres psql -U postgres -d mediaops < mediaops_dump.sql
```

### OpenSearch

- Index kann aus PostgreSQL neu aufgebaut werden via `/api/v1/assets/reindex`

## 8. Production Readiness Gaps (Current)

- Keine zentralen Metriken/Alerts
- Kein Secrets-Manager/Rotation
- Kein RBAC im Backend
- Kein dediziertes SLO/SLA-Set
- Kein Canary/Blue-Green Deployment
