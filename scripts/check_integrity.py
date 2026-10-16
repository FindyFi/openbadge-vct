#!/usr/bin/env python3
"""Check every "<name>#integrity" value in the repository's JSON files.

For each "<name>#integrity" key, the sibling "<name>" key holds the URL of
the protected file. URLs on this site are read from the repository; other
URLs are downloaded. The file's hash must match one of the SRI hashes
(sha256-, sha384- or sha512-, space separated) in the integrity value.

Run:  python3 scripts/check_integrity.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://openbadge.digicredential.eu/"
ALGORITHMS = {"sha256", "sha384", "sha512"}


def find_integrity(node, path=""):
    """Yield (location, url, integrity) for each #integrity key in node."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key.endswith("#integrity"):
                yield f"{path}/{key}", node.get(key[: -len("#integrity")]), value
            yield from find_integrity(value, f"{path}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from find_integrity(value, f"{path}/{i}")


def read(url: str) -> bytes:
    if url.startswith(SITE):
        return (ROOT / url[len(SITE):]).read_bytes()
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def check(url, integrity) -> str | None:
    """Return an error message, or None if the hash matches."""
    if not isinstance(url, str):
        return "no URL next to the integrity value"
    try:
        content = read(url)
    except (OSError, ValueError) as e:
        return f"can't read {url}: {e}"
    for sri in str(integrity).split():
        alg, _, expected = sri.partition("-")
        if alg in ALGORITHMS:
            actual = base64.b64encode(hashlib.new(alg, content).digest()).decode()
            if actual == expected:
                return None
    actual = base64.b64encode(hashlib.sha256(content).digest()).decode()
    return f"{url} has hash sha256-{actual}, expected {integrity}"


def main():
    checked, errors = 0, 0
    for json_file in sorted(ROOT.rglob("*.json")):
        if ".git" in json_file.parts:
            continue
        rel = json_file.relative_to(ROOT)
        for location, url, integrity in find_integrity(json.loads(json_file.read_text())):
            checked += 1
            error = check(url, integrity)
            if error:
                errors += 1
                print(f"::error file={rel}::{location}: {error}")
            else:
                print(f"ok  {rel}{location}")
    print(f"{checked} integrity values checked, {errors} wrong")
    sys.exit(1 if errors or not checked else 0)


if __name__ == "__main__":
    main()
