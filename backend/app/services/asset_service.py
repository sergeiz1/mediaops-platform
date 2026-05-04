from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetStatus
from app.models.asset import AssetVisibility
from app.core.config import settings
from app.repositories.asset_repository import (
    create_asset,
    delete_asset,
    get_asset_by_id,
    list_assets,
    update_asset,
)
from app.schemas.asset import AssetCreate, AssetUpdate
from app.workers.tasks.asset_tasks import process_asset_task


def get_assets(
    db: Session,
    query: str | None = None,
    status: AssetStatus | None = None,
    visibility: AssetVisibility | None = None,
    speaker: str | None = None,
    event_name: str | None = None,
    sort: str = "newest",
) -> list[Asset]:
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
    return create_asset(db, payload)


def update_asset_record(db: Session, asset_id: int, payload: AssetUpdate) -> Asset:
    asset = get_asset_or_404(db, asset_id)
    return update_asset(db, asset, payload)


def delete_asset_record(db: Session, asset_id: int) -> None:
    asset = get_asset_or_404(db, asset_id)
    delete_asset(db, asset)


def enqueue_asset_processing(db: Session, asset_id: int) -> None:
    asset = get_asset_or_404(db, asset_id)
    if asset.status == AssetStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset with id={asset_id} is already processing",
        )
    process_asset_task.delay(asset_id)


def build_upload_file_key(file_name: str) -> str:
    safe_name = file_name.replace("\\", "_").replace("/", "_").strip() or "upload.bin"
    return f"{uuid4()}-{safe_name}"


def resolve_storage_path(file_key: str) -> Path:
    storage_dir = Path(settings.media_storage_path).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / file_key
