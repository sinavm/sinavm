#!/usr/bin/env python3
"""Smoke-test the public GitHub Pages portal and portfolio."""
from __future__ import annotations

import os
import sys
import urllib.request

BASE = os.environ.get("SITE_BASE_URL", "https://sinavm.github.io/sinavm/").rstrip("/") + "/"
checks = {
    "": ["SiNAVM", "./portfolio/"],
    "portfolio/": ["Developer Portfolio", "portfolio.v1.css", "portfolio.v1.js", "#notes", "#contribute"],
    "portfolio/projects/svm.html": ["SVM", "AGPL-3.0", "svm-subscriptions.html"],
    "portfolio/projects/ir-net-atlas.html": ["IR Net Atlas", "MIT", "ir-net-atlas-measurement.html"],
    "portfolio/notes/svm-subscriptions.html": ["alive-fast", "alive-stable", "mix"],
    "portfolio/notes/ir-net-atlas-measurement.html": ["probe.py", "inside.json", "github-actions"],
}
failures = []
headers = {"User-Agent": "SiNAVM-Portfolio-Smoke/1.0"}

def fetch(url: str) -> tuple[int, str, str]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        body = response.read().decode("utf-8", "replace")
        return response.status, response.headers.get("Content-Type", ""), body

for path, markers in checks.items():
    url = BASE + path
    try:
        status, content_type, body = fetch(url)
        if status != 200 or "text/html" not in content_type:
            failures.append(f"{url}: unexpected HTTP/content type {status} {content_type}")
            continue
        for marker in markers:
            if marker not in body:
                failures.append(f"{url}: missing marker {marker!r}")
        print(f"OK {status} {url}")
    except Exception as exc:
        failures.append(f"{url}: {exc}")

for path in ("portfolio/assets/css/portfolio.v1.css", "portfolio/assets/js/portfolio.v1.js"):
    url = BASE + path
    try:
        status, content_type, body = fetch(url)
        if status != 200 or not body.strip():
            failures.append(f"{url}: empty or non-200 response ({status})")
        else:
            print(f"OK {status} {url} ({content_type})")
    except Exception as exc:
        failures.append(f"{url}: {exc}")

if failures:
    print("Live smoke test failed:")
    for failure in failures:
        print(f" - {failure}")
    sys.exit(1)
print("Live smoke test passed.")
