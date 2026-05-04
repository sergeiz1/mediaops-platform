from __future__ import annotations

from typing import Any

from opensearchpy import OpenSearch
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.asset import Asset, AssetStatus, AssetVisibility
from app.repositories.asset_repository import get_assets_by_ids


def _get_client() -> OpenSearch:
    return OpenSearch(hosts=[settings.opensearch_url], timeout=5)


def _ensure_index(client: OpenSearch) -> None:
    index_name = settings.opensearch_index
    if client.indices.exists(index=index_name):
        return

    client.indices.create(
        index=index_name,
        body={
            "mappings": {
                "properties": {
                    "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "description": {"type": "text"},
                    "speaker": {"type": "keyword"},
                    "event_name": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "visibility": {"type": "keyword"},
                    "uploaded_at": {"type": "date"},
                }
            }
        },
    )


def _is_enabled() -> bool:
    return settings.opensearch_enabled


def _document_from_asset(asset: Asset) -> dict[str, Any]:
    return {
        "title": asset.title,
        "description": asset.description,
        "speaker": asset.speaker,
        "event_name": asset.event_name,
        "status": asset.status.value,
        "visibility": asset.visibility.value,
        "uploaded_at": asset.uploaded_at.isoformat(),
    }


def upsert_asset_document(asset: Asset) -> None:
    if not _is_enabled():
        return
    try:
        client = _get_client()
        _ensure_index(client)
        client.index(
            index=settings.opensearch_index,
            id=asset.id,
            body=_document_from_asset(asset),
            refresh=True,
        )
    except Exception:
        return


def delete_asset_document(asset_id: int) -> None:
    if not _is_enabled():
        return
    try:
        client = _get_client()
        client.delete(index=settings.opensearch_index, id=asset_id, refresh=True, ignore=[404])
    except Exception:
        return


def reindex_assets(assets: list[Asset]) -> int:
    if not _is_enabled():
        return 0
    try:
        client = _get_client()
        _ensure_index(client)
        for asset in assets:
            client.index(
                index=settings.opensearch_index,
                id=asset.id,
                body=_document_from_asset(asset),
                refresh=False,
            )
        if assets:
            client.indices.refresh(index=settings.opensearch_index)
        return len(assets)
    except Exception:
        return 0


def search_assets(
    db: Session,
    query: str | None = None,
    status: AssetStatus | None = None,
    visibility: AssetVisibility | None = None,
    speaker: str | None = None,
    event_name: str | None = None,
    sort: str = "newest",
) -> list[Asset] | None:
    if not _is_enabled():
        return None

    try:
        client = _get_client()
        _ensure_index(client)

        must: list[dict[str, Any]] = []
        filter_terms: list[dict[str, Any]] = []

        if query:
            must.append(
                {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["title^3", "description"],
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "type": "phrase_prefix",
                                    "fields": ["title^3", "description"],
                                }
                            },
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )
        if status:
            filter_terms.append({"term": {"status": status.value}})
        if visibility:
            filter_terms.append({"term": {"visibility": visibility.value}})
        if speaker:
            must.append({"match_phrase_prefix": {"speaker": speaker}})
        if event_name:
            must.append({"match_phrase_prefix": {"event_name": event_name}})

        body: dict[str, Any] = {
            "query": {"bool": {"must": must, "filter": filter_terms}} if (must or filter_terms) else {"match_all": {}},
            "size": 200,
        }

        if sort == "oldest":
            body["sort"] = [{"uploaded_at": {"order": "asc"}}]
        elif sort == "title":
            body["sort"] = [{"title.keyword": {"order": "asc"}}]
        else:
            body["sort"] = [{"uploaded_at": {"order": "desc"}}]

        res = client.search(index=settings.opensearch_index, body=body)
        ids = [int(hit["_id"]) for hit in res.get("hits", {}).get("hits", [])]
        return get_assets_by_ids(db, ids)
    except Exception:
        return None
