#!/usr/bin/env python3
"""Safely insert verified ``//`` comments into RTL with legacy encodings.

Mode 2 must preserve every original source byte except the planned inserted
comments.  ``apply_patch`` cannot open many GB18030 RTL sources, so this
small, plan-driven helper provides the required encoding-aware write path.
It only accepts a UTF-8 JSON plan, requires a pre-edit format capture for
each source, and rejects any plan whose source cannot be decoded and encoded
back to exactly the original bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


def fail(message: str) -> None:
    raise ValueError(message)


def load_capture(path: Path) -> dict[str, object]:
    if not path.is_file():
        fail(f"format capture not found: {path}")
    try:
        capture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid format capture {path}: {exc}")
    encoding = capture.get("encoding")
    if encoding not in {"utf-8", "gb18030"}:
        fail(f"unsupported or unsafe source encoding in {path}: {encoding}")
    if capture.get("newline") not in {"lf", "crlf"}:
        fail(f"unsupported or unsafe newline convention in {path}: {capture.get('newline')}")
    return capture


def comment_block(lines: list[object], encoding: str, newline: str) -> bytes:
    if not lines:
        fail("a comment insertion needs at least one line")
    rendered: list[str] = []
    for line in lines:
        if not isinstance(line, str) or "\n" in line or "\r" in line:
            fail("each comment line must be a one-line string")
        if "*/" in line:
            fail("comment line may not include a block-comment terminator")
        rendered.append("//" if not line else f"// {line}")
    eol = "\r\n" if newline == "crlf" else "\n"
    return (eol.join(rendered) + eol).encode(encoding)


def entry_source(entry: dict[str, object], root: Path) -> Path:
    value = entry.get("source")
    if not isinstance(value, str) or not value:
        fail("plan entry has no source")
    source = (root / value).resolve()
    if not source.is_file() or source.is_symlink():
        fail(f"source must be a regular existing file: {source}")
    return source


def code_marker_positions(text: str, marker: str) -> list[int]:
    """Return occurrences not already inside a line comment.

    Historical RTL often retains whole prior implementations as ``//`` lines.
    A source-level marker may therefore appear both in active code and in
    historical comments.  Line comments never form an active Verilog token,
    so exclude only those occurrences; block-comment ambiguity remains a
    deliberate hard failure rather than a guess.
    """
    positions: list[int] = []
    start = 0
    while True:
        position = text.find(marker, start)
        if position < 0:
            return positions
        line_start = text.rfind("\n", 0, position) + 1
        if "//" not in text[line_start:position]:
            positions.append(position)
        start = position + 1


def apply_to_source(source: Path, entries: list[dict[str, object]], root: Path, write: bool) -> dict[str, object]:
    captures = {(root / str(entry["format_capture"])).resolve() for entry in entries}
    if len(captures) != 1:
        fail(f"each source must use one shared format capture: {source}")
    capture = load_capture(next(iter(captures)))
    encoding = str(capture["encoding"])
    raw = source.read_bytes()
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        fail(f"{source} is not decodable as captured {encoding}: {exc}")
    if text.encode(encoding) != raw:
        fail(f"{source} cannot round-trip losslessly as {encoding}")

    inserts: list[tuple[int, bytes, str]] = []
    seen_markers: set[str] = set()
    for entry in entries:
        marker = entry.get("insert_before")
        lines = entry.get("comments")
        if not isinstance(marker, str) or not marker:
            fail(f"plan entry has no insert_before marker: {source}")
        if marker in seen_markers:
            fail(f"duplicate marker for {source}: {marker!r}")
        seen_markers.add(marker)
        marker_positions = code_marker_positions(text, marker)
        count = len(marker_positions)
        if count != 1:
            fail(f"active-code marker must occur once in {source} (found {count}): {marker!r}")
        if not isinstance(lines, list):
            fail(f"comments must be a list for {source}: {marker!r}")
        position = marker_positions[0]
        byte_offset = len(text[:position].encode(encoding))
        inserts.append((byte_offset, comment_block(lines, encoding, str(capture["newline"])), marker))

    positions = [item[0] for item in inserts]
    if len(positions) != len(set(positions)):
        fail(f"two insertions resolve to the same byte offset in {source}")
    expected = raw
    for offset, block, _ in sorted(inserts, reverse=True):
        expected = expected[:offset] + block + expected[offset:]
    # This construction is the functional-byte proof: source bytes are used
    # untouched on both sides of each inserted ASCII line-comment block.
    if write:
        source.write_bytes(expected)
        if source.read_bytes() != expected:
            fail(f"write verification failed: {source}")
    return {
        "source": str(source),
        "encoding": encoding,
        "newline": capture["newline"],
        "insertions": len(inserts),
        "markers": [marker for _, _, marker in inserts],
        "applied": write,
    }


def verify_applied_source(source: Path, entries: list[dict[str, object]], root: Path) -> dict[str, object]:
    """Remove the exact planned blocks in memory and compare to pre-edit SHA."""
    captures = {(root / str(entry["format_capture"])).resolve() for entry in entries}
    if len(captures) != 1:
        fail(f"each source must use one shared format capture: {source}")
    capture = load_capture(next(iter(captures)))
    encoding = str(capture["encoding"])
    raw = source.read_bytes()
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        fail(f"{source} is not decodable as captured {encoding}: {exc}")
    if text.encode(encoding) != raw:
        fail(f"{source} cannot round-trip losslessly as {encoding}")

    inserted: list[tuple[int, bytes, str]] = []
    for entry in entries:
        marker = entry.get("insert_before")
        lines = entry.get("comments")
        if not isinstance(marker, str) or not isinstance(lines, list):
            fail(f"invalid plan entry for {source}")
        positions = code_marker_positions(text, marker)
        if len(positions) != 1:
            fail(f"active-code marker must occur once after insertion in {source}: {marker!r}")
        offset = len(text[:positions[0]].encode(encoding))
        block = comment_block(lines, encoding, str(capture["newline"]))
        if raw[offset - len(block):offset] != block:
            fail(f"planned comment block is not immediately before marker in {source}: {marker!r}")
        inserted.append((offset, block, marker))

    reconstructed = raw
    for offset, block, _ in sorted(inserted, reverse=True):
        reconstructed = reconstructed[:offset - len(block)] + reconstructed[offset:]
    original_sha = hashlib.sha256(reconstructed).hexdigest()
    if original_sha != capture.get("byte_sha256"):
        fail(f"non-comment bytes do not match pre-edit capture for {source}")
    return {
        "source": str(source),
        "encoding": encoding,
        "verified_insertions": len(inserted),
        "pre_edit_sha256_restored": original_sha,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Insert verified comment-only RTL annotations.")
    parser.add_argument("plan", type=Path, help="UTF-8 JSON under AI-work/annotations")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="perform the verified insertion; default is dry-run")
    mode.add_argument("--verify-applied", action="store_true", help="prove the planned blocks are the only changes")
    args = parser.parse_args(argv)
    plan = args.plan.resolve()
    if not plan.is_file() or "AI-work" not in plan.parts:
        print(f"FAIL: plan must be an existing file under AI-work: {plan}")
        return 2
    try:
        entries = json.loads(plan.read_text(encoding="utf-8"))
        if not isinstance(entries, list) or not entries:
            fail("plan must be a non-empty JSON list")
        root = Path.cwd().resolve()
        grouped: dict[Path, list[dict[str, object]]] = defaultdict(list)
        for item in entries:
            if not isinstance(item, dict):
                fail("every plan entry must be an object")
            if "format_capture" not in item:
                fail("every plan entry needs format_capture")
            grouped[entry_source(item, root)].append(item)
        if args.verify_applied:
            report = [verify_applied_source(source, items, root) for source, items in grouped.items()]
        else:
            report = [apply_to_source(source, items, root, args.apply) for source, items in grouped.items()]
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
