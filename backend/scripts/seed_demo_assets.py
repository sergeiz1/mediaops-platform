from __future__ import annotations

from app.core.database import SessionLocal
from app.models.asset import Asset, AssetStatus, AssetVisibility


SEED_ASSETS: list[dict] = [
    {
        "title": "Weekly Platform Sync",
        "description": "Team update on release scope and timeline.",
        "file_name": "weekly_platform_sync.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 1820,
        "speaker": "Mia Keller",
        "event_name": "Engineering Weekly",
        "status": AssetStatus.UPLOADED,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Incident Review Session",
        "description": "Review of service interruption and mitigation actions.",
        "file_name": "incident_review_session.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 2460,
        "speaker": "Noah Berger",
        "event_name": "Reliability Forum",
        "status": AssetStatus.UPLOADED,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Data Pipeline Walkthrough",
        "description": "Architecture walkthrough for ingestion and validation.",
        "file_name": "data_pipeline_walkthrough.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 3010,
        "speaker": "Lina Hoffmann",
        "event_name": "Architecture Review",
        "status": AssetStatus.PROCESSING,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Operations Handover",
        "description": "Shift handover notes and queue backlog overview.",
        "file_name": "operations_handover.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 1540,
        "speaker": "Elias Winter",
        "event_name": "Ops Handover",
        "status": AssetStatus.PROCESSING,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Security Controls Briefing",
        "description": "Access policy and controls review for service owners.",
        "file_name": "security_controls_briefing.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 2120,
        "speaker": "Sofia Brandt",
        "event_name": "Security Program",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Frontend UX Critique",
        "description": "Recorded UX session with feedback and action items.",
        "file_name": "frontend_ux_critique.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 1980,
        "speaker": "Clara Neumann",
        "event_name": "Design Review",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PUBLIC,
    },
    {
        "title": "Backend API Deep Dive",
        "description": "Endpoints, contracts, and error model discussion.",
        "file_name": "backend_api_deep_dive.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 3360,
        "speaker": "Felix Lang",
        "event_name": "Backend Guild",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Podcast Episode 04",
        "description": "Interview format on platform engineering practices.",
        "file_name": "podcast_episode_04.wav",
        "mime_type": "audio/wav",
        "duration_seconds": 2680,
        "speaker": "Nina Vogt",
        "event_name": "Engineering Podcast",
        "status": AssetStatus.READY,
        "visibility": AssetVisibility.PUBLIC,
    },
    {
        "title": "Mobile Upload Test Run",
        "description": "Validation run from mobile client with unstable network.",
        "file_name": "mobile_upload_test_run.mp4",
        "mime_type": "video/mp4",
        "duration_seconds": 840,
        "speaker": "Jan Ritter",
        "event_name": "QA Session",
        "status": AssetStatus.FAILED,
        "visibility": AssetVisibility.PRIVATE,
    },
    {
        "title": "Audio Normalization Batch",
        "description": "Batch processing validation with mixed sample rates.",
        "file_name": "audio_normalization_batch.wav",
        "mime_type": "audio/wav",
        "duration_seconds": 1260,
        "speaker": "Paul Meier",
        "event_name": "Media Processing QA",
        "status": AssetStatus.FAILED,
        "visibility": AssetVisibility.PRIVATE,
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        existing_titles = {row[0] for row in db.query(Asset.title).all()}
        to_create = [Asset(**payload) for payload in SEED_ASSETS if payload["title"] not in existing_titles]

        if to_create:
            db.add_all(to_create)
            db.commit()

        print(f"Inserted {len(to_create)} assets. Total seed set: {len(SEED_ASSETS)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
