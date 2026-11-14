#!/usr/bin/env python3
"""Mobile and interaction checks for the SiNAVM Ping dashboard."""
from __future__ import annotations

import os
import sys
from pathlib import Path
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


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
    )
    page = context.new_page()
    home_html = Path("index.html").read_text(encoding="utf-8")
    sitemap = Path("sitemap.xml").read_text(encoding="utf-8")
    ping_card_pos = home_html.find('href="https://sinavm.github.io/sinavm/sinavm-ping.html"')
    live_card_pos = home_html.find('href="https://sinavm.github.io/SVM/" class="action-btn httpcustom-btn"')
    check(ping_card_pos >= 0 and live_card_pos >= 0 and ping_card_pos < live_card_pos, "Homepage should place SiNAVM Ping before the live dashboard")
    check("sinavm-ping.html" in sitemap and "svm-ping.html" not in sitemap, "Sitemap should use the renamed canonical page only")
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    feed_lines = ["#announce: nodes=10 updated=2026-11-14T10:00:00Z"]
    for i in range(10):
        host = f"203.0.113.{10+i}"
        feed_lines.append(
            f"vless://11111111-1111-4111-8111-111111111111@{host}:443"
            f"?security=tls#Test%20Node%20{i+1}"
        )
    fast_feed = "\n".join(feed_lines) + "\n"
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

    def cloudflare(route):
        body = b"x" * 1000 if "bytes=1000" in route.request.url else b"x" * 1_000_000
        route.fulfill(
            status=200,
            headers={"access-control-allow-origin": "*", "cache-control": "no-store"},
            body=body,
        )

    page.route("https://203.0.113.*/**", lambda route: route.fulfill(status=200, headers={"cache-control":"no-store"}, body="probe-ok"))

    response = page.goto(BASE + "sinavm-ping.html", wait_until="domcontentloaded")
    check(response is not None and response.status == 200, "SiNAVM Ping page did not return HTTP 200")
    page.locator("#configs .config").first.wait_for(timeout=10000)
    check(page.locator("#configs .config").count() == 7, "Initial list should show exactly seven cards")
    check(page.locator("[data-more]").count() == 1, "Show more control should be visible")
    page.wait_for_function(
        "document.querySelector('.tag.country')?.textContent === 'Germany'",
        timeout=10000,
    )
    check(page.locator(".flag").first.inner_text() == "🇩🇪", "Country flag was not displayed")
    check("ms" in page.locator(".ping").first.inner_text(), "Published SVM delay was not displayed")

    page.locator("[data-more]").click()
    check(page.locator("#configs .config").count() == 10, "Show more should reveal the remaining nodes")
    check(page.locator("[data-more]").count() == 0, "Show more should disappear when all nodes are shown")

    page.locator("[data-details-id]").first.click()
    check(page.locator(".details.open").count() == 1, "Configuration details did not expand")
    page.locator("#search").fill("203.0.113.11")
    check(page.locator("#configs .config").count() == 1, "IP search did not filter results")
    page.locator("#search").fill("")

    page.locator("#start-node-test").click()
    page.wait_for_function(
        "document.querySelector('#user-probe-status')?.dataset.state === 'ok'",
        timeout=15000,
    )
    check("پاسخ HTTPS" in page.locator("#user-probe-status").inner_text(), "User-route probe did not report HTTPS reachability")
    check(page.locator("#user-probe-progress").evaluate("(el) => el.value") == 100, "User-route probe progress did not complete")
    check("زمان پاسخ HTTPS شما" in page.locator(".ping").first.inner_text(), "User-route latency was not shown on the config card")
    check("تأخیر اینترنت شما" in page.locator("#sortLabel").inner_text(), "Results were not switched to user-route latency sorting")

    no_horizontal_overflow(page, "390px Android layout")
    check(
        page.locator(".panel").first.evaluate("(el) => getComputedStyle(el).backdropFilter") == "none",
        "Backdrop blur should be disabled on mobile for smoother scrolling",
    )
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(100)
    page.evaluate("window.scrollTo(0, 0)")
    check(page.locator(".floating-tg-btn").count() == 1, "Floating Telegram button is missing")
    check(page.locator("#scrollTopBtn").count() == 1, "Scroll-to-top button is missing")
    check(page.locator("#visit-count").count() == 1, "Visitor counter is missing")
    check(page.locator('a[href*="legal_pages/privacy.html"]').count() == 1, "Privacy footer link is missing")

    page.set_viewport_size({"width": 320, "height": 740})
    no_horizontal_overflow(page, "320px Android layout")
    check(not page_errors, "JavaScript runtime errors: " + "; ".join(page_errors))
    legacy = page.goto(BASE + "svm-ping.html", wait_until="domcontentloaded")
    check(page.url.endswith("/sinavm-ping.html"), "Legacy URL should redirect to the new SiNAVM Ping URL")
    context.close()
    browser.close()

if errors:
    print("SiNAVM Ping browser checks failed:")
    for error in errors:
        print(" - " + error)
    sys.exit(1)
print("SiNAVM Ping checks passed: 7-item pagination, country flags, SVM delays, search, client-route latency/download, mobile rendering, footer and floating controls.")
