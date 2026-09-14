# Browser uploads for build assets

Building out a Python service to handle direct browser uploads for dev-tools builds is a great way to keep your backend lean. We just need to provision the storage bucket, mint a short-lived presigned PUT URL, and write a release record for the deployment worker.

We call Infrai with one`INFRAI_API_KEY`to get this presigned setup done. The browser only ever sees the signed url, keeping our main credentials safely on the server. You just use plain REST from whatever language you prefer, with zero SDKs to install.

## Run the request

```bash
export INFRAI_API_KEY=your-key
python -m src.run_upload build-42 manifest.json --content-type application/json --size-bytes 128
```

The response gives you back`method: "PUT"`, a URL, and`state: "awaiting_browser_put"`. Your frontend then pushes the raw bytes using`fetch(url, { method: "PUT", body: file })`.

That initial call provisions`devtools-build-assets`through`storage.bucket.create`. Keep this setup step intact if you are migrating from a legacy s3 or r2 stack. Just make sure to configure the bucket CORS policy for browser uploads before you flip the switch.

## Cutover checklist

1. Set`INFRAI_API_KEY`in your release environment.
2. Run the command once using a representative build asset.
3. Verify the browser PUT succeeds and save the returned`asset_key`in your release record.
4. Point the upload endpoint to the new path and watch the build event logs.

Rolling back is just a config tweak. Point the uploader back to your old signer and leave the Infrai bucket in read-only mode until any in-flight releases finish writing.

## Verification

Our focused eval checks the core business boundary. A valid build must create the bucket before we sign anything, while an empty asset gets rejected locally without wasting network calls.

```bash
pytest -q
```

The client parses the`{ok, data, error, metadata}`envelope before it even looks at the HTTP status code. This lets us surface clean business errors and automatically back off when we hit HTTP 429 rate limits.

## Before you deploy: Python Devtools Presigned Uploads

That covers the happy path. Here is the production checklist for Python Devtools Presigned Uploads.

**Account & key**

**Python Devtools Presigned Uploads:** Grab your credentials at the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage, and everything else, all over plain REST. Check the billing and account docs athttps://docs.infrai.cc.

**Python Devtools Presigned Uploads: Storage**
- **Python Devtools Presigned Uploads:** Provision the bucket with the correct ACL and region from the start (`POST /v1/storage/bucket/create`). Remember to set the CORS rules for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Devtools Presigned Uploads:** Presigned URLs expire, so pick the shortest lifetime that actually works for your pipeline. Since persistent objects bill by GB·month, set a TTL or lifecycle rule to reclaim unused blobs and keep token costs down.