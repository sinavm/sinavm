#!/usr/bin/env python3
"""Validate static portfolio HTML, local links, metadata and sitemap."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import html5lib

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://local.invalid/"
PAGES = [ROOT / "index.html", *sorted((ROOT / "portfolio").rglob("*.html"))]
errors: list[str] = []
parsed_docs = {}


def fail(message: str) -> None:
    errors.append(message)


def parse_page(path: Path):
    rel = path.relative_to(ROOT).as_posix()
    parser = html5lib.HTMLParser(strict=False, namespaceHTMLElements=False)
    try:
        document = parser.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{rel}: cannot parse HTML: {exc}")
        return None
    for error in parser.errors:
        (line, column), code, details = error
        fail(f"{rel}:{line}:{column}: HTML parse error {code} {details}")
    parsed_docs[path.resolve()] = document
    return document


def elements(document, name):
    return list(document.iter(name))


def page_url(path: Path) -> str:
    return urljoin(BASE, path.relative_to(ROOT).as_posix())


for page in PAGES:
    doc = parse_page(page)
    if doc is None:
        continue
    rel = page.relative_to(ROOT).as_posix()
    html = elements(doc, "html")
    heads = elements(doc, "head")
    titles = elements(doc, "title")
    h1s = elements(doc, "h1")
    if not html or html[0].get("lang") not in ("fa", "en"):
        fail(f"{rel}: html lang must be fa or en")
    if html and html[0].get("dir") not in ("rtl", "ltr"):
        fail(f"{rel}: html dir must be rtl or ltr")
    if not heads or not titles or not (titles[0].text or "").strip():
        fail(f"{rel}: missing document title")
    if rel.startswith("portfolio/") and len(h1s) != 1:
        fail(f"{rel}: expected exactly one h1, found {len(h1s)}")

    id_values = [node.get("id") for node in doc.iter() if node.get("id")]
    ids = set(id_values)
    if len(ids) != len(id_values):
        fail(f"{rel}: duplicate id attributes found")
    for node in doc.iter():
        if node.get("data-fa") is not None and node.get("data-en") is None:
            fail(f"{rel}: data-fa without data-en on <{node.tag}>")
        if node.get("data-en") is not None and node.get("data-fa") is None:
            fail(f"{rel}: data-en without data-fa on <{node.tag}>")
        if node.tag == "img" and node.get("alt") is None:
            fail(f"{rel}: img missing alt attribute")
        if rel.startswith("portfolio/") and node.tag == "a" and node.get("target") == "_blank":
            rel_tokens = set((node.get("rel") or "").lower().split())
            if not {"noopener", "noreferrer"}.issubset(rel_tokens):
                fail(f"{rel}: target=_blank link missing rel=noopener noreferrer")

        for attr in ("href", "src"):
            value = node.get(attr)
            if not value:
                continue
            absolute = urljoin(page_url(page), value)
            parsed = urlparse(absolute)
            if parsed.scheme not in ("https", "http") or parsed.netloc != "local.invalid":
                continue
            local_path = ROOT / unquote(parsed.path).lstrip("/")
            if parsed.path.endswith("/") or (local_path.exists() and local_path.is_dir()):
                local_path = local_path / "index.html"
            if not local_path.exists():
                fail(f"{rel}: broken local {attr}={value!r}")
                continue
            if parsed.fragment and local_path.suffix.lower() in (".html", ".htm"):
                target_doc = parsed_docs.get(local_path.resolve())
                if target_doc is None:
                    target_parser = html5lib.HTMLParser(strict=False, namespaceHTMLElements=False)
                    try:
                        target_doc = target_parser.parse(local_path.read_text(encoding="utf-8"))
                        parsed_docs[local_path.resolve()] = target_doc
                    except Exception:
                        target_doc = None
                if target_doc is not None:
                    target_ids = {item.get("id") for item in target_doc.iter() if item.get("id")}
                    if unquote(parsed.fragment) not in target_ids:
                        fail(f"{rel}: missing fragment #{parsed.fragment} in {local_path.relative_to(ROOT)}")

    if rel.startswith("portfolio/"):
        canonicals = [n.get("href") for n in doc.iter() if n.tag == "link" and "canonical" in (n.get("rel") or "").split()]
        if len(canonicals) != 1 or not canonicals[0].startswith("https://sinavm.github.io/sinavm/portfolio/"):
            fail(f"{rel}: expected one canonical URL under /portfolio/")
        hreflangs = {n.get("hreflang") for n in doc.iter() if n.tag == "link" and "alternate" in (n.get("rel") or "").split()}
        if not {"fa", "en", "x-default"}.issubset(hreflangs):
            fail(f"{rel}: missing fa/en/x-default alternate links")
        descriptions = [n.get("content", "") for n in doc.iter() if n.tag == "meta" and n.get("name") == "description"]
        if len(descriptions) != 1 or not descriptions[0].strip():
            fail(f"{rel}: expected one non-empty meta description")
        og_urls = [n.get("content") for n in doc.iter() if n.tag == "meta" and n.get("property") == "og:url"]
        if canonicals and (len(og_urls) != 1 or og_urls[0] != canonicals[0]):
            fail(f"{rel}: og:url must match canonical URL")
        for script in doc.iter("script"):
            if script.get("type") == "application/ld+json":
                try:
                    json.loads("".join(script.itertext()))
                except Exception as exc:
                    fail(f"{rel}: invalid JSON-LD: {exc}")

# The sitemap must be valid XML and include every portfolio HTML page.
sitemap = ROOT / "sitemap.xml"
try:
    tree = ET.parse(sitemap)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = {node.text for node in tree.findall(".//sm:loc", ns)}
    for location in locations:
        parsed_location = urlparse(location or "")
        if parsed_location.netloc != "sinavm.github.io":
            fail(f"sitemap.xml: unexpected host in {location}")
            continue
        site_path = unquote(parsed_location.path)
        if site_path == "/sinavm":
            site_path = "/"
        elif site_path.startswith("/sinavm/"):
            site_path = site_path[len("/sinavm"):]
        local = ROOT / site_path.lstrip("/")
        if site_path.endswith("/") or (local.exists() and local.is_dir()):
            local = local / "index.html"
        if not local.exists():
            fail(f"sitemap.xml: URL does not map to a local file: {location}")
    for page in sorted((ROOT / "portfolio").rglob("*.html")):
        doc = parsed_docs.get(page.resolve())
        canonical = None
        if doc is not None:
            canonical_nodes = [n for n in doc.iter() if n.tag == "link" and "canonical" in (n.get("rel") or "").split()]
            canonical = canonical_nodes[0].get("href") if len(canonical_nodes) == 1 else None
        if canonical and canonical not in locations:
            fail(f"sitemap.xml: missing {canonical}")
except Exception as exc:
    fail(f"sitemap.xml: invalid XML: {exc}")

if errors:
    print("Portfolio checks failed:")
    for item in errors:
        print(f" - {item}")
    sys.exit(1)
print(f"Portfolio checks passed: {len(PAGES)} HTML pages, local links, fragments, bilingual attributes, metadata and sitemap.")
