from sqlalchemy import or_, select
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
