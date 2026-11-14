#!/usr/bin/env python3
"""One-shot helper: decode staging/release.tar.b64.part* and extract the release tree."""
from __future__ import annotations

import base64
import hashlib
import sys
import tarfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "staging"
SUMS = STAGING / "SHA256SUMS"
PARTS = sorted(STAGING.glob("release.tar.b64.part*"))


def main() -> int:
    if not PARTS:
        print("No staging parts found", file=sys.stderr)
        return 1
    b64 = "".join(p.read_text() for p in PARTS)
    raw = base64.b64decode(b64)
    with tarfile.open(fileobj=BytesIO(raw), mode="r") as tar:
        try:
            tar.extractall(ROOT, filter="data")
        except TypeError:
            tar.extractall(ROOT)

    expected = {}
    for line in SUMS.read_text().splitlines():
        digest, path = line.split("  ", 1)
        expected[path] = digest

    missing, mismatch = [], []
    for path, digest in expected.items():
        fp = ROOT / path
        if not fp.is_file():
            missing.append(path)
            continue
        got = hashlib.sha256(fp.read_bytes()).hexdigest()
        if got != digest:
            mismatch.append(f"{path}: expected {digest} got {got}")
    if missing or mismatch:
        print("VERIFICATION FAILED", file=sys.stderr)
        for p in missing:
            print("missing", p, file=sys.stderr)
        for m in mismatch:
            print("mismatch", m, file=sys.stderr)
        return 1

    probe = ROOT / "charts/_encoding_test.bin"
    if probe.exists():
        probe.unlink()

    print(f"OK: verified {len(expected)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
