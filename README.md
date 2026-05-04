# Media Operations Platform

A showcase project for a modern multimedia platform focused on asset lifecycle management, asynchronous processing, operational visibility, and user-centric web workflows.

Built to demonstrate production-style engineering across frontend architecture, backend services, background processing, and clean system design.

---

## Project Goal

The main goal of Media Operations Platform is to provide a realistic foundation for a multimedia platform that can:

- manage uploaded media assets
- process media asynchronously
- expose operational states and job progress
- support search and discoverability
- prepare assets for publishing workflows
- offer a clean and user-centric web interface

This project is intentionally structured like a real product platform rather than a small demo application.

---

## Highlights

- Product-style platform architecture instead of a small demo app
- React + TypeScript frontend with routed application shell
- FastAPI backend with versioned API structure
- Asynchronous processing with Celery and Redis
- PostgreSQL-based asset persistence with Alembic migrations
- OpenSearch-backed search with automatic indexing and reindex endpoint
- Foundation for media upload, processing, monitoring, and publishing workflows

---

## Why This Project

This project is intentionally built as a realistic platform engineering showcase.

Instead of focusing on isolated CRUD screens, it demonstrates how a multimedia platform can be structured across frontend, backend, processing workflows, and operational concerns. The emphasis is on maintainability, modularity, and production-oriented design.

---

## Core Use Cases

The platform is planned around the following use cases:

- Upload media assets such as video or audio files
- Store and manage metadata for each asset
- Trigger processing workflows in the background
- Track processing jobs and operational states
- Display assets in a searchable management interface
- Prepare media for publishing and delivery workflows

---

## Architecture Overview

The system follows a service-oriented structure with a dedicated frontend, backend API, and background worker layer.

### Planned architecture components

- **Frontend**
  - React + TypeScript + Vite
  - routing, layout, dashboard, asset management pages

- **Backend API**
  - FastAPI
  - versioned REST API endpoints
  - business logic for assets, jobs, uploads, and health monitoring

- **Database**
  - PostgreSQL
  - persistent storage for assets, jobs, and metadata

- **Background Processing**
  - Celery + Redis
  - asynchronous processing for media workflows

- **Storage**
  - local storage in early development
  - later MinIO / S3-compatible object storage

- **Search**
  - OpenSearch integration for asset discovery and filtering
  - fallback to PostgreSQL query filtering when OpenSearch is unavailable

---

## Tech Stack

### Frontend
- React
- TypeScript
- Vite
- SCSS
- React Router
- Axios

### Backend
- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic Settings

### Planned Infrastructure
- PostgreSQL
- Redis
- Celery
- MinIO
- Docker Compose
- OpenSearch

---

## Project Structure

```text
mediaops-platform/
├─ backend/
│  ├─ alembic/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ models/
│  │  ├─ repositories/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  └─ workers/
│  └─ alembic.ini
├─ frontend/
│  ├─ public/
│  └─ src/
│     ├─ api/
│     ├─ app/
│     ├─ components/
│     ├─ features/
│     ├─ pages/
│     ├─ styles/
│     └─ types/
├─ docs/
├─ infra/
├─ storage/
├─ docker-compose.yml
└─ README.md
```

---

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`.


### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`.

Health endpoint: `http://localhost:8000/api/v1/health`

### Infrastructure (PostgreSQL + Redis + OpenSearch)

```bash
docker compose up -d postgres redis opensearch
```

PostgreSQL is exposed on `localhost:5433`.
OpenSearch is exposed on `http://localhost:9200`.

### Migrations

```bash
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

### Celery Worker (Windows)

```bash
cd backend
.\run_worker.ps1
```

### Celery Worker (macOS / Linux)

```bash
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app:celery_app worker --loglevel=info
```

### Seed Data (10 assets)

```bash
cd backend
.\.venv\Scripts\python.exe -m scripts.seed_cern_assets
```

### OpenSearch Reindex

```bash
curl -X POST http://localhost:8000/api/v1/assets/reindex
```

---

## Roadmap

- [x] Frontend shell and route structure
- [x] Backend API skeleton
- [x] Health endpoint
- [x] Frontend-backend integration
- [x] Asset domain model
- [x] PostgreSQL integration
- [x] Alembic migrations
- [x] Asset CRUD
- [x] Background job processing
- [x] Media upload workflow
- [x] Search and filtering
- [x] OpenSearch integration (indexing, querying, reindex endpoint)
- [x] Frontend GUI completion (assets, upload, jobs, filters, actions)

---

## Author

Showcase project by Serge Z.  
Software Engineer | Platform Architecture | Full-Stack Development
