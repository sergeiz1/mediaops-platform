from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetStatus
from app.models.asset import AssetVisibility
from app.core.config import settings
from app.repositories.asset_repository import (
    create_asset,
    delete_asset,
    get_asset_by_id,
    get_asset_stats,
    list_assets,
    update_asset,
)
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services.search_service import (
    delete_asset_document,
    reindex_assets,
    search_assets,
    upsert_asset_document,
)
from app.workers.tasks.asset_tasks import process_asset_task
from app.workers.celery_app import celery_app


def get_assets(
    db: Session,
    query: str | None = None,
    status: AssetStatus | None = None,
    visibility: AssetVisibility | None = None,
    speaker: str | None = None,
    event_name: str | None = None,
    sort: str = "newest",
) -> list[Asset]:
    has_search_filters = any([query, status, visibility, speaker, event_name])

    # Keep the canonical library view consistent with dashboard metrics:
    # when no search/filter is applied, always read directly from Postgres.
    if not has_search_filters:
        return list_assets(
            db,
            query=query,
            status=status,
            visibility=visibility,
            speaker=speaker,
            event_name=event_name,
            sort=sort,
        )

    search_results = search_assets(
        db,
        query=query,
        status=status,
        visibility=visibility,
        speaker=speaker,
        event_name=event_name,
        sort=sort,
    )
    if search_results is not None:
        return search_results

    return list_assets(
        db,
        query=query,
        status=status,
        visibility=visibility,
        speaker=speaker,
        event_name=event_name,
        sort=sort,
    )


def get_asset_or_404(db: Session, asset_id: int) -> Asset:
    asset = get_asset_by_id(db, asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id={asset_id} not found",
        )
    return asset


def create_asset_record(db: Session, payload: AssetCreate) -> Asset:
    asset = create_asset(db, payload)
    upsert_asset_document(asset)
    return asset


def update_asset_record(db: Session, asset_id: int, payload: AssetUpdate) -> Asset:
    asset = get_asset_or_404(db, asset_id)
    asset = update_asset(db, asset, payload)
    upsert_asset_document(asset)
    return asset


def delete_asset_record(db: Session, asset_id: int) -> None:
    asset = get_asset_or_404(db, asset_id)
    delete_asset(db, asset)
    delete_asset_document(asset_id)


def enqueue_asset_processing(db: Session, asset_id: int) -> None:
    asset = get_asset_or_404(db, asset_id)
    if asset.status == AssetStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset with id={asset_id} is already processing",
        )
    asset.status = AssetStatus.PROCESSING
    asset.processing_started_at = datetime.now(timezone.utc)
    asset.processing_finished_at = None
    asset.last_error = None
    db.add(asset)
    db.commit()
    db.refresh(asset)
    upsert_asset_document(asset)

    try:
        process_asset_task.delay(asset_id)
    except Exception as exc:
        asset.status = AssetStatus.FAILED
        asset.processing_finished_at = datetime.now(timezone.utc)
        asset.last_error = f"Queue dispatch failed: {exc}"[:500]
        db.add(asset)
        db.commit()
        db.refresh(asset)
        upsert_asset_document(asset)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not enqueue processing job. Check Redis/Celery worker.",
        ) from exc


def build_upload_file_key(file_name: str) -> str:
    safe_name = file_name.replace("\\", "_").replace("/", "_").strip() or "upload.bin"
    return f"{uuid4()}-{safe_name}"


def resolve_storage_path(file_key: str) -> Path:
    storage_dir = Path(settings.media_storage_path).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / file_key


def reindex_all_assets(db: Session) -> int:
    assets = list_assets(db, sort="newest")
    return reindex_assets(assets)


def get_dashboard_stats(db: Session, days: int = 7) -> dict:
    stats = get_asset_stats(db, days=days)
    worker_online = False
    try:
        replies = celery_app.control.inspect(timeout=0.5).ping() or {}
        worker_online = len(replies) > 0
    except Exception:
        worker_online = False
    stats["worker_online"] = worker_online
    return stats


def resolve_processing_asset(db: Session, asset_id: int, target_status: AssetStatus) -> Asset:
    asset = get_asset_or_404(db, asset_id)
    if asset.status != AssetStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset with id={asset_id} is not in processing state",
        )
    if target_status not in (AssetStatus.READY, AssetStatus.FAILED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid target status")

    asset.status = target_status
    asset.processing_finished_at = datetime.now(timezone.utc)
    if target_status == AssetStatus.FAILED and not asset.last_error:
        asset.last_error = "Manually marked as failed by user"
    if target_status == AssetStatus.READY:
        asset.last_error = None

    db.add(asset)
    db.commit()
    db.refresh(asset)
    upsert_asset_document(asset)
    return asset
