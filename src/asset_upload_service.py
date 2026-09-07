from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .infrai_client import InfraiClient

# Canonical capability shape for readers: infrai.storage.object.presign


@dataclass(frozen=True)
class BuildAsset:
    build_id: str
    filename: str
    content_type: str
    size_bytes: int


@dataclass(frozen=True)
class UploadPlan:
    key: str
    upload_url: str
    method: str = "PUT"


class AssetUploadService:
    def __init__(self, client: InfraiClient, bucket: str = "devtools-build-assets"):
        self.client = client
        self.bucket = bucket

    def prepare(self, asset: BuildAsset) -> UploadPlan:
        if asset.size_bytes <= 0:
            raise ValueError("asset size_bytes must be positive")
        if "/" in asset.filename or "\\" in asset.filename:
            raise ValueError("filename must be a leaf name")
        key = f"builds/{asset.build_id}/{asset.filename}"
        signed = self.client.presign(self.bucket, key, content_type=asset.content_type, max_bytes=asset.size_bytes)
        return UploadPlan(key=key, upload_url=signed["url"])

    def release_record(self, asset: BuildAsset, plan: UploadPlan) -> dict[str, Any]:
        return {"build_id": asset.build_id, "asset_key": plan.key, "state": "awaiting_browser_put"}


def build_upload_plan(client: InfraiClient, asset: BuildAsset) -> UploadPlan:
    return AssetUploadService(client).prepare(asset)
