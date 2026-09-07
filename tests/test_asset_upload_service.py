import pytest

from src.asset_upload_service import AssetUploadService, BuildAsset


class FakeClient:
    def __init__(self):
        self.calls = []

    def create_bucket(self, name):
        self.calls.append(("create_bucket", name))

    def presign(self, bucket, key, *, content_type, max_bytes):
        self.calls.append(("presign", bucket, key, content_type, max_bytes))
        return {"url": "https://upload.example/signed"}


def test_prepare_scopes_put_url_without_creating_persistent_resources():
    client = FakeClient()
    asset = BuildAsset("build-42", "manifest.json", "application/json", 128)
    plan = AssetUploadService(client).prepare(asset)
    assert plan.key == "builds/build-42/manifest.json"
    assert plan.method == "PUT"
    assert client.calls == [
        ("presign", "devtools-build-assets", "builds/build-42/manifest.json", "application/json", 128),
    ]


def test_rejects_empty_asset_before_remote_calls():
    with pytest.raises(ValueError):
        AssetUploadService(FakeClient()).prepare(BuildAsset("b", "x.js", "text/javascript", 0))
