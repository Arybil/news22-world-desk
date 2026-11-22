#!/usr/bin/env python3
"""Validate entry.png, then stage it into the make.fun output directory.

Exits 0 on success. Exits 2 when the source file is missing or unreadable,
1 when validation fails, and 3 when the output directory cannot be used.
Every error message names the file and the actual value vs. the limit.
"""
import os
import shutil
import sys

SRC = "entry.png"
MAX_DIM = 1024
MAX_BYTES = 1 << 20
PNG_SIG = b"\x89PNG\r\n\x1a\n"


class ValidationError(Exception):
    pass


def read_header(path):
    with open(path, "rb") as fh:
        return fh.read(24)


def check_file(path):
    """Return a list of human-readable problems; empty list means valid."""
    problems = []
    if not os.path.isfile(path):
        raise ValidationError(
            "%s: file not found — run from the repo root where entry.png lives" % path
        )
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        problems.append(
            "%s: size %d B exceeds limit %d B (%d B over — re-render smaller)"
            % (path, size, MAX_BYTES, size - MAX_BYTES)
        )
    header = read_header(path)
    if len(header) < 24 or header[:8] != PNG_SIG:
        problems.append(
            "%s: bad PNG signature (expected %r, got %r — not a valid PNG)"
            % (path, PNG_SIG, header[:8])
        )
        return problems
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    if width > MAX_DIM or height > MAX_DIM:
        problems.append(
            "%s: dimensions %dx%d exceed limit %dx%d"
            % (path, width, height, MAX_DIM, MAX_DIM)
        )
    return problems


def stage_output(out_dir):
    """Ensure the output dir exists and is writable; raise if not."""
    try:
        os.makedirs(out_dir, exist_ok=True)
        probe = os.path.join(out_dir, ".write-test")
        with open(probe, "wb"):
            pass
        os.remove(probe)
    except OSError as exc:
        raise ValidationError(
            "output dir %r is not usable: %s (fix permissions or pick another "
            "MAKEFUN_OUTPUT_DIR)" % (out_dir, exc)
        ) from exc


def main():
    problems = []
    try:
        problems = check_file(SRC)
        out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
        stage_output(out_dir)
    except ValidationError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2 if "not found" in str(exc) or "not usable" in str(exc) else 1
    if problems:
        for problem in problems:
            print("error: %s" % problem, file=sys.stderr)
        return 1
    dest = os.path.join(out_dir, "entry.png")
    shutil.copy2(SRC, dest)
    print("staged %s -> %s" % (SRC, dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
