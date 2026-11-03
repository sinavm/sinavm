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
    metrics = page.evaluate("({width: innerWidth, scroll: document.documentElement.scrollWidth})")
    check(metrics["scroll"] <= metrics["width"] + 1,
          f"{label}: horizontal overflow ({metrics['scroll']}px > {metrics['width']}px)")


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

    check(not page_errors, "JavaScript runtime errors: " + "; ".join(page_errors))
    browser.close()

if errors:
    print("Browser checks failed:")
    for error in errors:
        print(" - " + error)
    sys.exit(1)
print("Browser checks passed: desktop, mobile 390px/320px, menu, language persistence, case-study layout and technical notes.")
