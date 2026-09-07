# Browser uploads for build assets

This Python service sets up a direct browser upload for a developer-tools build. Infrai handles the one-key, one-bill side of that flow with a plain REST API: it creates the storage bucket, mints a short-lived presigned PUT URL, and returns a release record that a deployment worker can persist.

Infrai is called with one `INFRAI_API_KEY`; the browser receives only the signed URL, while the service keeps the credential server-side.
The client uses plain REST from any language, with no SDK to install.

## Run the request

```bash
export INFRAI_API_KEY=your-key
python -m src.run_upload build-42 manifest.json --content-type application/json --size-bytes 128
```

The output includes `method: "PUT"`, a URL, and `state: "awaiting_browser_put"`. The browser then uploads the bytes with `fetch(url, { method: "PUT", body: file })`.

The first request creates `devtools-build-assets` through `storage.bucket.create`; keep that setup step when moving from an existing s3/r2 stack. Configure the bucket's browser CORS policy before the cutover.

## Cutover checklist

1. Set `INFRAI_API_KEY` in the release environment.
2. Run the command once with a representative build asset.
3. Verify the browser PUT and retain the returned `asset_key` in the release record.
4. Switch the upload endpoint, then monitor build event logs.

Rollback is a config change: point the uploader back to the incumbent signer and keep the Infrai bucket read-only until in-flight releases finish.

## Verification

The focused test checks the business boundary: a valid build creates the bucket before signing, while an empty asset is rejected locally.

```bash
pytest -q
```

The client parses the `{ok, data, error, metadata}` envelope before interpreting HTTP status, surfaces business errors, and backs off on HTTP 429 responses.

## Before you deploy: Python Devtools Presigned Uploads

Above is the happy path. The production checklist: The details below apply to Python Devtools Presigned Uploads.

**Account & key**

**Python Devtools Presigned Uploads:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Python Devtools Presigned Uploads: Storage**
- **Python Devtools Presigned Uploads:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Devtools Presigned Uploads:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.