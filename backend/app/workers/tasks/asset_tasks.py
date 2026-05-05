from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.asset import Asset, AssetStatus
from app.services.search_service import upsert_asset_document
from app.workers.celery_app import celery_app


@celery_app.task(name="asset.process")
def process_asset_task(asset_id: int) -> None:
    db: Session = SessionLocal()
    try:
        asset = db.get(Asset, asset_id)
        if asset is None:
            return

        now = datetime.now(timezone.utc)
        asset.status = AssetStatus.PROCESSING
        asset.processing_started_at = now
        asset.processing_finished_at = None
        asset.last_error = None
        db.add(asset)
        db.commit()
        db.refresh(asset)
        upsert_asset_document(asset)

        # Placeholder for future ffprobe/ffmpeg processing pipeline.
        time.sleep(2)

        finished_at = datetime.now(timezone.utc)
        asset.status = AssetStatus.READY
        asset.processing_finished_at = finished_at
        asset.last_error = None
        db.add(asset)
        db.commit()
        db.refresh(asset)
        upsert_asset_document(asset)
    except Exception as exc:
        asset = db.get(Asset, asset_id)
        if asset is not None:
            asset.status = AssetStatus.FAILED
            asset.processing_finished_at = datetime.now(timezone.utc)
            asset.last_error = str(exc)[:500]
            db.add(asset)
            db.commit()
            db.refresh(asset)
            upsert_asset_document(asset)
        raise
    finally:
        db.close()
