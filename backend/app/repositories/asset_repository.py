from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetStatus, AssetVisibility
from app.schemas.asset import AssetCreate, AssetUpdate


def list_assets(
    db: Session,
    query: str | None = None,
    status: AssetStatus | None = None,
    visibility: AssetVisibility | None = None,
    speaker: str | None = None,
    event_name: str | None = None,
    sort: str = "newest",
) -> list[Asset]:
    stmt = select(Asset)

    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(or_(Asset.title.ilike(pattern), Asset.description.ilike(pattern)))

    if status is not None:
        stmt = stmt.where(Asset.status == status)

    if visibility is not None:
        stmt = stmt.where(Asset.visibility == visibility)

    if speaker:
        stmt = stmt.where(Asset.speaker.ilike(f"%{speaker}%"))

    if event_name:
        stmt = stmt.where(Asset.event_name.ilike(f"%{event_name}%"))

    if sort == "oldest":
        stmt = stmt.order_by(Asset.uploaded_at.asc())
    elif sort == "title":
        stmt = stmt.order_by(Asset.title.asc())
    else:
        stmt = stmt.order_by(Asset.uploaded_at.desc())

    return list(db.scalars(stmt).all())


def get_asset_by_id(db: Session, asset_id: int) -> Asset | None:
    return db.get(Asset, asset_id)


def get_assets_by_ids(db: Session, asset_ids: list[int]) -> list[Asset]:
    if not asset_ids:
        return []
    rows = list(db.scalars(select(Asset).where(Asset.id.in_(asset_ids))).all())
    row_map = {row.id: row for row in rows}
    return [row_map[asset_id] for asset_id in asset_ids if asset_id in row_map]


def create_asset(db: Session, payload: AssetCreate) -> Asset:
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def update_asset(db: Session, asset: Asset, payload: AssetUpdate) -> Asset:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset: Asset) -> None:
    db.delete(asset)
    db.commit()


def get_asset_stats(db: Session, days: int = 7) -> dict:
    total_assets = db.scalar(select(func.count(Asset.id))) or 0

    status_rows = db.execute(
        select(Asset.status, func.count(Asset.id)).group_by(Asset.status)
    ).all()
    by_status = {status.value if hasattr(status, "value") else str(status): count for status, count in status_rows}

    mime_rows = db.execute(
        select(Asset.mime_type, func.count(Asset.id)).group_by(Asset.mime_type)
    ).all()
    by_mime_type = {(mime or "unknown"): count for mime, count in mime_rows}

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(days - 1, 0))
    day_bucket = func.date_trunc("day", Asset.uploaded_at)
    upload_rows = db.execute(
        select(day_bucket, func.count(Asset.id))
        .where(Asset.uploaded_at >= cutoff)
        .group_by(day_bucket)
        .order_by(day_bucket.asc())
    ).all()
    uploads_per_day = [
        {"date": bucket.date().isoformat(), "count": count}
        for bucket, count in upload_rows
        if bucket is not None
    ]

    pending_jobs = (by_status.get("uploaded", 0) or 0) + (by_status.get("processing", 0) or 0)

    avg_runtime_seconds = 0.0
    median_runtime_seconds = 0.0
    last_runtime_seconds = 0.0
    failure_insights: list[dict] = []
    recent_upload_assets = list_recent_uploads(db, limit=8)
    recent_processing_assets: list[Asset] = []
    recent_failed_assets: list[Asset] = []

    # Compatibility fallback: if extended columns are not yet migrated in a running DB,
    # keep stats endpoint alive and still return core KPI values.
    try:
        runtime_rows = db.execute(
            select(
                func.extract("epoch", Asset.processing_finished_at - Asset.processing_started_at).label("runtime")
            ).where(
                Asset.status == AssetStatus.READY,
                Asset.processing_started_at.is_not(None),
                Asset.processing_finished_at.is_not(None),
            )
        ).all()
        runtimes = [float(row.runtime) for row in runtime_rows if row.runtime is not None and float(row.runtime) >= 0]
        avg_runtime_seconds = (sum(runtimes) / len(runtimes)) if runtimes else 0.0
        if runtimes:
            sorted_runtimes = sorted(runtimes)
            mid = len(sorted_runtimes) // 2
            if len(sorted_runtimes) % 2 == 0:
                median_runtime_seconds = (sorted_runtimes[mid - 1] + sorted_runtimes[mid]) / 2
            else:
                median_runtime_seconds = sorted_runtimes[mid]

        last_runtime_row = db.execute(
            select(func.extract("epoch", Asset.processing_finished_at - Asset.processing_started_at))
            .where(
                Asset.processing_started_at.is_not(None),
                Asset.processing_finished_at.is_not(None),
            )
            .order_by(Asset.processing_finished_at.desc())
            .limit(1)
        ).first()
        if last_runtime_row and last_runtime_row[0] is not None:
            last_runtime_seconds = max(float(last_runtime_row[0]), 0.0)

        failure_rows = db.execute(
            select(
                func.coalesce(func.nullif(Asset.last_error, ""), "Unknown failure"),
                func.count(Asset.id),
            )
            .where(Asset.status == AssetStatus.FAILED)
            .group_by(func.coalesce(func.nullif(Asset.last_error, ""), "Unknown failure"))
            .order_by(func.count(Asset.id).desc())
            .limit(5)
        ).all()
        failure_insights = [{"reason": str(reason), "count": count} for reason, count in failure_rows]

        recent_processing_assets = (
            db.scalars(
                select(Asset)
                .where(Asset.processing_started_at.is_not(None))
                .order_by(Asset.processing_started_at.desc())
                .limit(8)
            )
            .all()
        )
        if len(recent_processing_assets) == 0:
            # Backward-compatible fallback for rows that were processed before
            # processing_started_at existed/populated.
            recent_processing_assets = (
                db.scalars(
                    select(Asset)
                    .where(
                        (Asset.status == AssetStatus.PROCESSING)
                        | (
                            (Asset.status == AssetStatus.READY)
                            & (Asset.updated_at > Asset.uploaded_at)
                        ),
                    )
                    .order_by(Asset.updated_at.desc())
                    .limit(8)
                )
                .all()
            )
        recent_failed_assets = list_recent_failures(db, limit=8)
    except Exception:
        failure_insights = []
        recent_processing_assets = []
        recent_failed_assets = []

    return {
        "total_assets": total_assets,
        "by_status": by_status,
        "by_mime_type": by_mime_type,
        "uploads_per_day": uploads_per_day,
        "pending_jobs": pending_jobs,
        "processing_funnel": {
            "uploaded": by_status.get("uploaded", 0) or 0,
            "processing": by_status.get("processing", 0) or 0,
            "ready": by_status.get("ready", 0) or 0,
            "failed": by_status.get("failed", 0) or 0,
        },
        "failure_insights": failure_insights,
        "time_to_ready": {
            "avg_seconds": round(avg_runtime_seconds, 2),
            "median_seconds": round(median_runtime_seconds, 2),
            "last_runtime_seconds": round(last_runtime_seconds, 2),
        },
        "recent_activity": {
            "uploads": [
                {"id": asset.id, "title": asset.title, "at": asset.uploaded_at.isoformat()}
                for asset in recent_upload_assets
            ],
            "process_starts": [
                {
                    "id": asset.id,
                    "title": asset.title,
                    "at": (
                        asset.processing_started_at
                        or asset.processing_finished_at
                        or asset.updated_at
                    ).isoformat(),
                }
                for asset in recent_processing_assets
            ],
            "fails": [
                {
                    "id": asset.id,
                    "title": asset.title,
                    "at": asset.updated_at.isoformat(),
                    "reason": asset.last_error or "Unknown failure",
                }
                for asset in recent_failed_assets
            ],
        },
    }


def list_recent_uploads(db: Session, limit: int = 8) -> list[Asset]:
    stmt = select(Asset).order_by(Asset.uploaded_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def list_recent_processing_starts(db: Session, limit: int = 8) -> list[Asset]:
    stmt = (
        select(Asset)
        .where(Asset.status == AssetStatus.PROCESSING)
        .order_by(Asset.updated_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def list_recent_failures(db: Session, limit: int = 8) -> list[Asset]:
    stmt = (
        select(Asset)
        .where(Asset.status == AssetStatus.FAILED)
        .order_by(Asset.updated_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
