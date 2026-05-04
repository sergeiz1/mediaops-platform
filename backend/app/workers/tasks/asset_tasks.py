from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.asset import Asset, AssetStatus
from app.workers.celery_app import celery_app


@celery_app.task(name="asset.process")
def process_asset_task(asset_id: int) -> None:
    db: Session = SessionLocal()
    try:
        asset = db.get(Asset, asset_id)
        if asset is None:
            return

        asset.status = AssetStatus.PROCESSING
        db.add(asset)
        db.commit()

        # Placeholder for future ffprobe/ffmpeg processing pipeline.
        time.sleep(2)

        asset.status = AssetStatus.READY
        db.add(asset)
        db.commit()
    except Exception:
        asset = db.get(Asset, asset_id)
        if asset is not None:
            asset.status = AssetStatus.FAILED
            db.add(asset)
            db.commit()
        raise
    finally:
        db.close()
