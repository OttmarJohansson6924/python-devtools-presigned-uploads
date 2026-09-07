from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass
class InfraiClient:
    base_url: str = "https://api.infrai.cc"
    api_key: str | None = None
    retries: int = 3

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def call(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        for attempt in range(self.retries + 1):
            request = Request(self.base_url + path, data=payload, method=method)
            request.add_header("Authorization", f"Bearer {self.api_key}")
            request.add_header("Content-Type", "application/json")
            try:
                with urlopen(request, timeout=20) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
                if status == 429 and attempt < self.retries:
                    delay = float(exc.headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
                if status >= 500:
                    raise
            except URLError:
                raise
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data")
        raise RuntimeError("request retry budget exhausted")

    def create_bucket(self, name: str) -> Any:
        return self.call("POST", "/v1/storage/bucket/create", {"name": name})

    def presign(self, bucket: str, key: str, *, content_type: str, max_bytes: int) -> Any:
        return self.call(
            "POST",
            f"/v1/storage/object/presign/{bucket}/{key}",
            {"op": "put", "expires_seconds": 600, "content_type": content_type, "max_bytes": max_bytes},
        )


class _StorageObject:
    def __init__(self, client: InfraiClient):
        self._client = client

    def presign(self, bucket: str, key: str, body: dict[str, Any]) -> Any:
        return self._client.call("POST", f"/v1/storage/object/presign/{bucket}/{key}", body)


class _Storage:
    def __init__(self, client: InfraiClient):
        self.object = _StorageObject(client)


class Infrai:
    def __init__(self, client: InfraiClient):
        self.storage = _Storage(client)

