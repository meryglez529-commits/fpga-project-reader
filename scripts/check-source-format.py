#!/usr/bin/env python3
"""Capture or verify source encoding and newline convention for Mode 2.

The script deliberately does not rewrite a source file. A captured JSON record
must be written under AI-work/annotations/ so annotation checks leave no files
beside the user's RTL.
"""

from __future__ import annotations

import argparse

import hashlib
import json
import sys
from pathlib import Path


def describe(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        encoding, bom = "utf-8", True
    else:
        try:
            data.decode("utf-8")
            encoding, bom = "utf-8", False
        except UnicodeDecodeError:
            try:
                data.decode("gb18030")
                encoding, bom = "gb18030", False
            except UnicodeDecodeError:
                encoding, bom = "unknown", False
    crlf = data.count(b"\r\n")
    lf_only = data.replace(b"\r\n", b"").count(b"\n")
    if crlf and lf_only:
        newline = "mixed"
    elif crlf:
        newline = "crlf"
    elif lf_only:
        newline = "lf"
    else:
        newline = "none"
    return {
        "source": str(path.resolve()), "encoding": encoding, "bom": bom,
        "newline": newline, "byte_sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
    }


def under_ai_work(path: Path) -> bool:
    return "AI-work" in path.resolve().parts


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Capture/verify RTL source format without editing it.")
    parser.add_argument("source", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-json", type=Path, help="capture to an AI-work/annotations JSON file")
    group.add_argument("--expected-json", type=Path, help="compare encoding/BOM/newline against capture")
    args = parser.parse_args(argv)
    if not args.source.is_file():
        print(f"FAIL: source not found: {args.source}")
        return 2
    current = describe(args.source)
    if args.write_json:
        if not under_ai_work(args.write_json):
            print(f"FAIL: format capture must be under AI-work: {args.write_json}")
            return 2
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"PASS: captured {args.source} -> {args.write_json}")
        return 0
    if not args.expected_json.is_file():
        print(f"FAIL: expected JSON not found: {args.expected_json}")
        return 2
    expected = json.loads(args.expected_json.read_text(encoding="utf-8"))
    fields = ("encoding", "bom", "newline")
    mismatch = [field for field in fields if expected.get(field) != current.get(field)]
    if mismatch:
        print(f"FAIL: format changed in {args.source}: {', '.join(mismatch)}")
        return 1
    print(f"PASS: format preserved for {args.source} ({current['encoding']}, {current['newline']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
