import argparse
import json

from .asset_upload_service import AssetUploadService, BuildAsset
from .infrai_client import InfraiClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint a browser PUT URL for a build asset")
    parser.add_argument("build_id")
    parser.add_argument("filename")
    parser.add_argument("--content-type", default="application/octet-stream")
    parser.add_argument("--size-bytes", type=int, required=True)
    args = parser.parse_args()
    asset = BuildAsset(args.build_id, args.filename, args.content_type, args.size_bytes)
    service = AssetUploadService(InfraiClient())
    plan = service.prepare(asset)
    print(json.dumps({"upload": plan.__dict__, "release": service.release_record(asset, plan)}, indent=2))


if __name__ == "__main__":
    main()

