#!/usr/bin/env python3
"""Exercise the portfolio in Chromium at desktop and mobile viewports."""
from __future__ import annotations

import os
import sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get("SITE_BASE_URL", "http://127.0.0.1:8765/").rstrip("/") + "/"
PORTFOLIO = BASE + "portfolio/"
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
        return {tag: el.tagName, id: el.id, className: typeof el.className === 'string' ? el.className : '', left: Math.round(r.left), right: Math.round(r.right), scrollWidth: el.scrollWidth, clientWidth: el.clientWidth};
      }).filter(x => x.right > innerWidth + 1 || x.left < -1).slice(0, 8)
    })""")
    check(metrics["scroll"] <= metrics["width"] + 1,
          f"{label}: horizontal overflow ({metrics['scroll']}px > {metrics['width']}px); elements={metrics['offenders']}")


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    response = page.goto(PORTFOLIO, wait_until="domcontentloaded")
    check(response is not None and response.status == 200, "desktop: portfolio did not return HTTP 200")
    page.locator("#main-content h1").wait_for()
    check(page.locator("#primary-navigation").is_visible(), "desktop: primary navigation should be visible")
    check(not page.locator("#menu-toggle").is_visible(), "desktop: mobile menu toggle should be hidden")
    check(page.locator("#lang-toggle").is_visible(), "desktop: language toggle should be visible")
    no_horizontal_overflow(page, "desktop 1440px")

    # The existing portal must expose the portfolio without replacing its own homepage.
    portal = browser.new_page(viewport={"width": 390, "height": 844})
    portal.on("pageerror", lambda error: page_errors.append("portal: " + str(error)))
    portal_response = portal.goto(BASE, wait_until="domcontentloaded")
    check(portal_response is not None and portal_response.status == 200, "portal: homepage did not return HTTP 200")
    check(portal.locator(".portfolio-entry").is_visible(), "portal: portfolio entry link is missing or hidden")
    check(portal.locator(".portfolio-entry").get_attribute("href") == "./portfolio/", "portal: portfolio entry has the wrong destination")
    no_horizontal_overflow(portal, "portal mobile 390px")
    portal.close()

    # Mobile navigation, language switching and persisted preference.
    page.set_viewport_size({"width": 390, "height": 844})
    page.reload(wait_until="domcontentloaded")
    check(page.locator("#menu-toggle").is_visible(), "mobile: menu toggle should be visible")
    check(not page.locator("#primary-navigation").is_visible(), "mobile: menu should start closed")
    page.locator("#menu-toggle").click()
    check(page.locator("#primary-navigation").is_visible(), "mobile: menu did not open")
    check(page.locator("#menu-toggle").get_attribute("aria-expanded") == "true", "mobile: aria-expanded not updated")
    page.locator('#primary-navigation a[href="#projects"]').click()
    check(not page.locator("#primary-navigation").is_visible(), "mobile: menu did not close after navigation")
    page.locator("#lang-toggle").click()
    check(page.locator("html").get_attribute("lang") == "en", "language toggle did not switch to English")
    check(page.locator("html").get_attribute("dir") == "ltr", "English direction should be LTR")
    check(page.evaluate("localStorage.getItem('sinavm-portfolio-language')") == "en",
          "language preference was not persisted")
    page.reload(wait_until="domcontentloaded")
    check(page.locator("html").get_attribute("lang") == "en", "language preference did not survive reload")
    no_horizontal_overflow(page, "mobile 390px")

    # Narrow mobile and case-study layout.
    page.set_viewport_size({"width": 320, "height": 740})
    no_horizontal_overflow(page, "mobile 320px")
    page.goto(PORTFOLIO + "projects/ir-net-atlas.html", wait_until="domcontentloaded")
    check(page.locator("html").get_attribute("lang") == "en", "language preference did not persist across pages")
    check(page.locator(".architecture").is_visible(), "case study architecture diagram is missing")
    columns = page.locator(".architecture").evaluate("el => getComputedStyle(el).gridTemplateColumns.split(' ').length")
    check(columns == 1, f"mobile case study: expected one architecture column, found {columns}")
    no_horizontal_overflow(page, "case study 320px")

    # Technical note pages share the same language and responsive layout.
    page.goto(PORTFOLIO + "notes/svm-subscriptions.html", wait_until="domcontentloaded")
    check(page.locator("main h1").is_visible(), "technical note heading is missing")
    check(page.locator("pre code").count() >= 1, "technical note reproducible command is missing")
    no_horizontal_overflow(page, "technical note 320px")

    # SVM ping dashboard: deterministic mocked feeds, report, geolocation and responsive layout.
    svm_page = browser.new_page(viewport={"width": 390, "height": 844})
    svm_page_errors: list[str] = []
    svm_page.on("pageerror", lambda error: svm_page_errors.append(str(error)))
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
    svm_page.route(
        "**/lite/subscriptions/xray/normal/alive-fast*",
        lambda route: route.fulfill(status=200, content_type="text/plain", body=fast_feed),
    )
    svm_page.route(
        "**/lite/subscriptions/xray/normal/alive-stable*",
        lambda route: route.fulfill(status=200, content_type="text/plain", body=stable_feed),
    )
    svm_page.route(
        "**/lite/reports/test.json*",
        lambda route: route.fulfill(status=200, content_type="application/json", body=report_body),
    )
    svm_page.route(
        "https://ipwho.is/**",
        lambda route: route.fulfill(status=200, content_type="application/json", body=geo_body),
    )
    svm_response = svm_page.goto(BASE + "svm-ping.html", wait_until="domcontentloaded")
    check(svm_response is not None and svm_response.status == 200, "SVM ping: page did not return HTTP 200")
    svm_page.locator("#configs .config").first.wait_for(timeout=10000)
    check(svm_page.locator("#configs .config").count() == 1, "SVM ping: fast feed was not rendered")
    svm_page.wait_for_function(
        "document.querySelector('.tag.country')?.textContent === 'Germany'",
        timeout=10000,
    )
    check("ms" in svm_page.locator(".ping").first.inner_text(), "SVM ping: published delay was not displayed")
    check(svm_page.locator(".flag").first.inner_text() == "🇩🇪", "SVM ping: country flag was not displayed")
    svm_page.locator("#search").fill("203.0.113.10")
    check(svm_page.locator("#configs .config").count() == 1, "SVM ping: IP search did not filter results")
    no_horizontal_overflow(svm_page, "SVM ping mobile 390px")
    svm_page.locator('[data-feed="stable"]').click()
    svm_page.locator("#configs .config").first.wait_for(timeout=10000)
    check(
        svm_page.locator(".tag.protocol").first.inner_text() == "TROJAN",
        "SVM ping: stable feed tab did not switch protocols",
    )
    svm_page.set_viewport_size({"width": 320, "height": 740})
    no_horizontal_overflow(svm_page, "SVM ping mobile 320px")
    check(not svm_page_errors, "SVM ping JavaScript runtime errors: " + "; ".join(svm_page_errors))
    svm_page.close()

    check(not page_errors, "JavaScript runtime errors: " + "; ".join(page_errors))
    browser.close()

if errors:
    print("Browser checks failed:")
    for error in errors:
        print(" - " + error)
    sys.exit(1)
print("Browser checks passed: desktop, mobile 390px/320px, menu, language persistence, case-study layout and technical notes.")
