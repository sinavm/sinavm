#!/usr/bin/env python3
"""Browser smoke tests for the SVM ping dashboard with deterministic mocked APIs."""
from __future__ import annotations

import os
import sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get("SITE_BASE_URL", "http://127.0.0.1:8766/").rstrip("/") + "/"
errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def no_horizontal_overflow(page, label: str) -> None:
    metrics = page.evaluate("""() => ({
      width: innerWidth,
      scroll: document.documentElement.scrollWidth,
      offenders: [...document.querySelectorAll('body *')].map(el => {
        const r = el.getBoundingClientRect();
        return {tag: el.tagName, id: el.id, className: typeof el.className === 'string' ? el.className : '', left: Math.round(r.left), right: Math.round(r.right)};
      }).filter(x => x.right > innerWidth + 1 || x.left < -1).slice(0, 8)
    })""")
    check(metrics["scroll"] <= metrics["width"] + 1,
          f"{label}: horizontal overflow ({metrics['scroll']}px > {metrics['width']}px); elements={metrics['offenders']}")


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    fast_feed = (
        "#announce: nodes=1 updated=2026-11-14T10:00:00Z\n"
        "vless://11111111-1111-4111-8111-111111111111@203.0.113.10:443?security=tls#Test%20Node\n"
    )
    stable_feed = (
        "#announce: nodes=1 updated=2026-11-14T10:00:00Z\n"
        "trojan://password@198.51.100.20:443?security=tls#Stable%20Node\n"
    )
    report_body = (
        '{"engine":"sing-box-test","tested_at":"2026-11-14T10:00:00Z",'
        '"input":2,"kept":1,"infra_ok":true,'
        '"fastest":[{"tag":"n0001","type":"vless","delay":42,"host":"203.0.113.10"}]}'
    )
    geo_body = (
        '{"success":true,"country":"Germany","country_code":"DE",'
        '"flag":{"emoji":"🇩🇪"}}'
    )
    page.route(
        "**/lite/subscriptions/xray/normal/alive-fast*",
        lambda route: route.fulfill(status=200, content_type="text/plain", body=fast_feed),
    )
    page.route(
        "**/lite/subscriptions/xray/normal/alive-stable*",
        lambda route: route.fulfill(status=200, content_type="text/plain", body=stable_feed),
    )
    page.route(
        "**/lite/reports/test.json*",
        lambda route: route.fulfill(status=200, content_type="application/json", body=report_body),
    )
    page.route(
        "https://ipwho.is/**",
        lambda route: route.fulfill(status=200, content_type="application/json", body=geo_body),
    )
    response = page.goto(BASE + "svm-ping.html", wait_until="domcontentloaded")
    check(response is not None and response.status == 200, "SVM ping: page did not return HTTP 200")
    page.locator("#configs .config").first.wait_for(timeout=10000)
    check(page.locator("#configs .config").count() == 1, "SVM ping: fast feed was not rendered")
    page.wait_for_function(
        "document.querySelector('.tag.country')?.textContent === 'Germany'",
        timeout=10000,
    )
    check("ms" in page.locator(".ping").first.inner_text(), "SVM ping: published delay was not displayed")
    check(page.locator(".flag").first.inner_text() == "🇩🇪", "SVM ping: country flag was not displayed")
    page.locator("#search").fill("203.0.113.10")
    check(page.locator("#configs .config").count() == 1, "SVM ping: IP search did not filter results")
    no_horizontal_overflow(page, "SVM ping mobile 390px")
    page.locator('[data-feed="stable"]').click()
    page.locator("#configs .config").first.wait_for(timeout=10000)
    check(
        page.locator(".tag.protocol").first.inner_text() == "TROJAN",
        "SVM ping: stable feed tab did not switch protocols",
    )
    page.set_viewport_size({"width": 320, "height": 740})
    no_horizontal_overflow(page, "SVM ping mobile 320px")
    check(not page_errors, "SVM ping JavaScript runtime errors: " + "; ".join(page_errors))
    browser.close()

if errors:
    print("SVM ping browser checks failed:")
    for error in errors:
        print(" - " + error)
    sys.exit(1)
print("SVM ping browser checks passed: feed loading, real-report rendering, country flag, search, tabs and mobile layouts.")
