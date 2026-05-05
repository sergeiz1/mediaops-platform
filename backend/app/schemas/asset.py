from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.asset import AssetStatus, AssetVisibility

class AssetBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    file_key: str | None = None
    file_name: str = Field(min_length=1, max_length=512)
    mime_type: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    speaker: str | None = None
    event_name: str | None = None
    visibility: AssetVisibility = AssetVisibility.PRIVATE


class AssetCreate(AssetBase):
    status: AssetStatus = AssetStatus.UPLOADED


class AssetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    speaker: str | None = None
    event_name: str | None = None
    status: AssetStatus | None = None
    visibility: AssetVisibility | None = None
    published_at: datetime | None = None


class AssetRead(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: AssetStatus
    uploaded_at: datetime
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    processing_started_at: datetime | None = None
    processing_finished_at: datetime | None = None
    last_error: str | None = None


class AssetUploadResponse(BaseModel):
    asset: AssetRead
    stored_path: str
