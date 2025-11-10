#!/usr/bin/env python3
"""
Generate packs_manifest.json for Godot PCK packs.

Output format (example):
{
  "enemies.pck":     {"version": "b1a2c3...","size": 1234567,"mtime":"2025-11-10T08:33:12Z","sha256":"b1a2c3..."},
  "environment.pck": {"version": "d4e5f6...","size": 7654321,"mtime":"2025-11-09T19:10:05Z","sha256":"d4e5f6..."}
}

Usage:
  python make_manifest.py --dir ./public --out ./public/packs_manifest.json
  python make_manifest.py --dir ./UkrBirdsPacks
"""
import argparse, hashlib, json, os, sys, time
from datetime import datetime, timezone

def iso8601_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(description="Generate packs_manifest.json for .pck files.")
    ap.add_argument("--dir", required=True, help="Directory containing .pck files")
    ap.add_argument("--out", default=None, help="Output manifest path (default: <dir>/packs_manifest.json)")
    ap.add_argument("--pattern", default=".pck", help="File suffix to include (default: .pck)")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = ap.parse_args()

    base_dir = os.path.abspath(args.dir)
    if not os.path.isdir(base_dir):
        print(f"[ERR] Not a directory: {base_dir}", file=sys.stderr)
        sys.exit(1)

    out_path = args.out or os.path.join(base_dir, "packs_manifest.json")

    manifest = {}
    for name in sorted(os.listdir(base_dir)):
        if not name.endswith(args.pattern):
            continue
        full_path = os.path.join(base_dir, name)
        if not os.path.isfile(full_path):
            continue
        st = os.stat(full_path)
        size = int(st.st_size)
        mtime = iso8601_utc(st.st_mtime)
        digest = sha256_file(full_path)

        # Fields:
        # - version: used by your game code as cache-busting query param (?v=...)
        # - size/mtime/sha256: informative; your loader uses size optionally; sha256 is good for audits
        manifest[name] = {
            "version": digest,     # your Godot code will use this in _build_pack_url(..., version)
            "size": size,
            "mtime": mtime,
            "sha256": digest
        }

    json_kwargs = {"indent": 2, "sort_keys": True} if args.pretty else {}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, **json_kwargs)
        f.write("\n")

    print(f"[OK] Wrote {out_path} with {len(manifest)} entries.")

if __name__ == "__main__":
    main()
