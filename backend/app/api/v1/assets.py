from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.auth_deps import require_min_role
from app.core.database import get_db
from app.models.asset import AssetStatus, AssetVisibility
from app.models.user import UserRole
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate, AssetUploadResponse
from app.services.asset_service import (
    build_upload_file_key,
    create_asset_record,
    delete_asset_record,
    enqueue_asset_processing,
    get_asset_or_404,
    get_assets,
    get_dashboard_stats,
    reindex_all_assets,
    resolve_processing_asset,
    resolve_storage_path,
    update_asset_record,
)

router = APIRouter(prefix="/assets")


@router.get("", response_model=list[AssetRead])
def list_assets_endpoint(
    q: str | None = Query(default=None),
    status_filter: AssetStatus | None = Query(default=None, alias="status"),
    visibility: AssetVisibility | None = Query(default=None),
    speaker: str | None = Query(default=None),
    event_name: str | None = Query(default=None),
    sort: Literal["newest", "oldest", "title"] = Query(default="newest"),
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.VIEWER)),
) -> list[AssetRead]:
    return get_assets(
        db,
        query=q,
        status=status_filter,
        visibility=visibility,
        speaker=speaker,
        event_name=event_name,
        sort=sort,
    )


@router.get("/stats")
def get_asset_stats_endpoint(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.VIEWER)),
) -> dict:
    return get_dashboard_stats(db, days=days)


@router.post("/reindex", status_code=status.HTTP_202_ACCEPTED)
def reindex_assets_endpoint(
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.EDITOR)),
) -> dict[str, int]:
    indexed = reindex_all_assets(db)
    return {"indexed": indexed}


@router.get("/reindex", status_code=status.HTTP_200_OK)
def reindex_assets_endpoint_get(
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.EDITOR)),
) -> dict[str, int]:
    indexed = reindex_all_assets(db)
    return {"indexed": indexed}


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset_endpoint(
    asset_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.VIEWER)),
) -> AssetRead:
    return get_asset_or_404(db, asset_id)


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset_endpoint(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.EDITOR)),
) -> AssetRead:
    return create_asset_record(db, payload)


@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset_endpoint(
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.EDITOR)),
) -> AssetRead:
    return update_asset_record(db, asset_id, payload)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_endpoint(
    asset_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.ADMIN)),
) -> Response:
    delete_asset_record(db, asset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{asset_id}/process", status_code=status.HTTP_202_ACCEPTED)
def process_asset_endpoint(
    asset_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.EDITOR)),
) -> dict[str, str]:
    enqueue_asset_processing(db, asset_id)
    return {"status": "accepted"}


@router.post("/{asset_id}/mark-ready", response_model=AssetRead)
def mark_ready_endpoint(
    asset_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.EDITOR)),
) -> AssetRead:
    return resolve_processing_asset(db, asset_id, AssetStatus.READY)


@router.post("/{asset_id}/mark-failed", response_model=AssetRead)
def mark_failed_endpoint(
    asset_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.EDITOR)),
) -> AssetRead:
    return resolve_processing_asset(db, asset_id, AssetStatus.FAILED)


@router.post("/upload", response_model=AssetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset_endpoint(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(default=None),
    speaker: str | None = Form(default=None),
    event_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
    _: object = Depends(require_min_role(UserRole.EDITOR)),
) -> AssetUploadResponse:
    file_key = build_upload_file_key(file.filename or "upload.bin")
    stored_path = resolve_storage_path(file_key)
    content = await file.read()
    stored_path.write_bytes(content)

    asset = create_asset_record(
        db,
        AssetCreate(
            title=title,
            description=description,
            file_key=file_key,
            file_name=file.filename or "upload.bin",
            mime_type=file.content_type,
            speaker=speaker,
            event_name=event_name,
        ),
    )
    return AssetUploadResponse(asset=asset, stored_path=str(stored_path))
