#!/usr/bin/env python3
"""Mobile and interaction checks for the current SiNAVM Ping dashboard."""
from __future__ import annotations

import os
import sys
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

BASE = os.environ.get("SITE_BASE_URL", "http://127.0.0.1:8766/").rstrip("/") + "/"
errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def no_horizontal_overflow(page, label: str) -> None:
    metrics = page.evaluate("""() => ({width: innerWidth, scroll: document.documentElement.scrollWidth})""")
    check(metrics["scroll"] <= metrics["width"] + 1,
          f"{label}: horizontal overflow ({metrics['scroll']}px > {metrics['width']}px)")


fast_lines = ["#announce: nodes=10 updated=2026-11-14T10:00:00Z"]
for i in range(10):
    host = f"203.0.113.{10+i}"
    fast_lines.append(
        f"vless://11111111-1111-4111-8111-111111111111@{host}:443"
        f"?security=tls#Test%20Node%20{i+1}"
    )
fast_feed = "\n".join(fast_lines) + "\n"
stable_feed = (
    "#announce: nodes=1 updated=2026-11-14T10:00:00Z\n"
    "trojan://password@198.51.100.20:443?security=tls#Stable%20Node\n"
)
report_body = (
    '{"engine":"sing-box-test","tested_at":"2026-11-14T10:00:00Z",'
    '"input":10,"kept":10,"infra_ok":true,'
    '"fastest":[{"tag":"n0001","type":"vless","delay":42,"host":"203.0.113.10"},'
    '{"tag":"n0002","type":"vless","delay":55,"host":"203.0.113.11"},'
    '{"tag":"n0003","type":"vless","delay":61,"host":"203.0.113.12"}]}'
)
geo_body = (
    '{"success":true,"country":"Germany","country_code":"DE",'
    '"flag":{"emoji":"🇩🇪"}}'
)


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
    )
    page = context.new_page()
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))

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
    page.route(
        "https://page-views.count1.workers.dev/**",
        lambda route: route.fulfill(status=200, content_type="text/plain", body="1234"),
    )

    def cloudflare(route):
        query = parse_qs(urlparse(route.request.url).query)
        size = int(query.get("bytes", ["1000"])[0])
        route.fulfill(
            status=200,
            headers={"access-control-allow-origin": "*", "cache-control": "no-store"},
            body=b"x" * size,
        )

    page.route("https://speed.cloudflare.com/**", cloudflare)

    response = page.goto(BASE + "sinavm-ping.html", wait_until="domcontentloaded")
    check(response is not None and response.status == 200, "SiNAVM Ping page did not return HTTP 200")
    page.locator("#configs .config").first.wait_for(timeout=15000)
    page.wait_for_function(
        "document.querySelector('.tag.country')?.textContent === 'Germany'",
        timeout=15000,
    )

    check(page.locator("#configs .config").count() == 7, "Initial Fast list should show seven cards")
    check(page.locator("[data-more]").count() == 1, "Show more control should be visible")
    check(page.locator("#stat-kept").inner_text() == "۱۰", "SVM report kept count was not rendered")
    check(page.locator(".flag").first.inner_text() == "🇩🇪", "Country flag was not displayed")
    check("42" in page.locator(".ping").first.inner_text(), "Published SVM delay was not displayed")

    page.locator("[data-more]").click()
    check(page.locator("#configs .config").count() == 10, "Show more should reveal all ten nodes")
    check(page.locator("[data-more]").count() == 0, "Show more should disappear when all nodes are shown")

    page.locator("[data-details-id]").first.click()
    check(page.locator(".details.open").count() == 1, "Configuration details did not expand")
    page.locator("#search").fill("203.0.113.11")
    check(page.locator("#configs .config").count() == 1, "IP search did not filter results")
    page.locator("#search").fill("")

    page.locator('[data-feed="stable"]').click()
    page.locator("#configs .config").first.wait_for(timeout=10000)
    check(page.locator("#configs .config").count() == 1, "Stable tab did not load its own feed")
    page.locator('[data-feed="fast"]').click()
    page.locator("#configs .config").first.wait_for(timeout=10000)
    check(page.locator("#configs .config").count() == 7, "Switching back to Fast did not restore the Fast feed")

    page.locator("#start-client-test").click()
    page.wait_for_function(
        "document.querySelector('#network-status')?.dataset.state === 'ok'",
        timeout=15000,
    )
    check(page.locator("#client-latency").inner_text() not in ("—", "…"),
          "Client-route latency was not displayed")
    check(page.locator("#client-download").inner_text() not in ("—", "…"),
          "Client-route download speed was not displayed")
    check("تست اتصال دستگاه کامل شد" in page.locator("#network-status").inner_text(),
          "Client-route test did not report completion")

    no_horizontal_overflow(page, "390px Android layout")
    check(
        page.locator(".panel").first.evaluate("(el) => getComputedStyle(el).backdropFilter") == "none",
        "Backdrop blur should be disabled on mobile for smoother scrolling",
    )
    check(page.locator(".floating-tg-btn").count() == 1, "Floating Telegram button is missing")
    check(page.locator("#scrollTopBtn").count() == 1, "Scroll-to-top button is missing")
    check(page.locator("#visit-count").count() == 1, "Visitor counter is missing")
    check(page.locator('a[href*="legal_pages/privacy.html"]').count() == 1, "Privacy footer link is missing")

    page.set_viewport_size({"width": 320, "height": 740})
    no_horizontal_overflow(page, "320px Android layout")
    check(not page_errors, "JavaScript runtime errors: " + "; ".join(page_errors))
    context.close()
    browser.close()

if errors:
    print("SiNAVM Ping browser checks failed:")
    for error in errors:
        print(" - " + error)
    sys.exit(1)
print("SiNAVM Ping checks passed: live feeds, report metrics, country flags, SVM delays, search, pagination, feed switching, client-route latency/download and mobile rendering.")
