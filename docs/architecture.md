# Architecture - MediaOps Platform

## 1. Scope

MediaOps Platform ist als modulare Web-Plattform für den Lebenszyklus von Multimedia-Assets gedacht:

- Upload
- Metadaten-Verwaltung
- asynchrone Verarbeitung
- Suche und Discovery
- Publishing
- operations-nahe Sicht auf Systemzustände

Dieses Dokument beschreibt das Zielbild und den aktuellen Umsetzungsstand.

## 2. Current Status (Roadmap Alignment)

Bereits umgesetzt:

- Frontend shell and route structure
- Backend API skeleton
- Health endpoint

In Arbeit / nächste Schritte:

- Frontend-backend integration
- Asset domain model
- PostgreSQL integration
- Alembic migrations
- Asset CRUD
- Background job processing
- Media upload workflow
- Search and filtering

## 3. Logical Architecture

Die Plattform ist in vier Hauptschichten aufgeteilt:

1. Frontend (React + TypeScript)
2. API Service (FastAPI)
3. Worker Service (Celery)
4. Data/Infra Layer (PostgreSQL, Redis, Object Storage, Search)

### 3.1 Frontend

Verantwortung:

- Upload- und Management-UI für Assets
- Statusdarstellung (uploaded, processing, ready, failed)
- Filter- und Suchinteraktionen
- Publishing- und Detailansichten
- Admin-/Operations-Übersicht

Schnittstelle:

- REST API (`/api/v1/...`)

### 3.2 API Service

Verantwortung:

- Auth (MVP: einfacher JWT-basierter Login)
- Asset-CRUD
- Validierung von Requests
- Erzeugung von Upload-Workflows
- Triggern von Background Jobs
- Health/Readiness-Endpunkte

Schnittstellen:

- Frontend <-> FastAPI
- FastAPI <-> PostgreSQL
- FastAPI <-> Redis/Celery
- FastAPI <-> Object Storage

### 3.3 Worker Service

Verantwortung:

- asynchrone Medienverarbeitung
- Metadaten-Extraktion (z. B. ffprobe)
- Thumbnail-Erzeugung (z. B. ffmpeg)
- Fehlerbehandlung und Retry-Strategie
- Rückschreiben von Job-/Asset-Status

Schnittstellen:

- Celery Queue (Redis Broker)
- PostgreSQL für Job- und Asset-Status
- Object Storage für Input/Output-Artefakte

### 3.4 Data and Infrastructure Layer

- PostgreSQL: Source of truth für Assets, Jobs, Nutzer, Metadaten
- Redis: Queue/Broker für asynchrone Tasks
- Object Storage (initial lokal, später MinIO/S3): Medien und Derived Assets
- OpenSearch (Phase 2+): Volltextsuche und Filter-Performance

## 4. Core Domain Model (Target)

### 4.1 Asset

- `id`
- `title`
- `description`
- `file_name`
- `mime_type`
- `duration`
- `speaker`
- `event_name`
- `uploaded_at`
- `published_at`
- `status`
- `visibility`

### 4.2 ProcessingJob

- `id`
- `asset_id`
- `type`
- `status`
- `started_at`
- `finished_at`
- `error_message`

### 4.3 Transcript (optional, Phase 3)

- `id`
- `asset_id`
- `language`
- `full_text`

### 4.4 Tag

- `id`
- `name`

## 5. Primary Workflows

### 5.1 Upload and Process

1. User legt Asset-Metadaten an und lädt Datei hoch.
2. API persistiert Asset mit Status `uploaded`.
3. API enqueued ProcessingJob.
4. Worker verarbeitet Asset und aktualisiert Job/Asset-Status.
5. UI pollt/abonniert Status bis `ready` oder `failed`.

### 5.2 Search and Discovery

1. User setzt Suchbegriff und Filter.
2. API führt Suche zunächst in PostgreSQL aus (MVP).
3. In Phase 2 übernimmt OpenSearch Volltext-/Filterlogik.
4. UI zeigt sortierte Ergebnisse inkl. Status und Metadaten.

### 5.3 Publishing

1. User setzt Asset auf `public` oder `private`.
2. API speichert Sichtbarkeit und optional `published_at`.
3. UI generiert Detail-/Share-Ansicht für veröffentlichte Inhalte.

## 6. Deployment and Runtime (Target)

Lokale Entwicklungsumgebung via Docker Compose:

- `frontend`
- `api`
- `worker`
- `postgres`
- `redis`
- `minio` (ab Upload-Workflow-Ausbau)

Später erweiterbar für Kubernetes/OpenShift (separate Deployments/Services pro Komponente).

## 7. Non-Functional Priorities

- klare Service-Grenzen (API vs Worker)
- idempotente Job-Verarbeitung
- nachvollziehbare Statusübergänge
- fehlertolerante Queue-Verarbeitung
- migrationsbasierte Datenbankevolution (Alembic)
- observability-fähige Struktur (Logs/Metriken vorbereitbar)

## 8. Immediate Next Implementation Steps

1. Frontend mit Backend-Health und Basis-Asset-Endpoints verdrahten.
2. SQLAlchemy-Modelle für `Asset` und `ProcessingJob` implementieren.
3. PostgreSQL-Connection + Session-Management einführen.
4. Erste Alembic-Migration erzeugen.
5. Asset-CRUD-Endpunkte mit persistenter DB-Schicht bereitstellen.
