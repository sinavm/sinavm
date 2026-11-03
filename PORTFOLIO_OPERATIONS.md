# Portfolio release and operations

## What is published

GitHub Pages serves this repository from `main` at the repository root. The existing portal remains at `/`; the developer portfolio is served from `/portfolio/`. Project case studies and technical notes are ordinary static HTML files beneath that directory.

## Before publishing

Run locally or in CI:

```bash
python -m pip install --require-hashes -r requirements-checks.txt
python scripts/check_portfolio.py
node --check portfolio/assets/js/portfolio.v1.js
python -m pip install --require-hashes -r requirements-browser.txt
python -m playwright install chromium
python -m http.server 8765 &
SITE_BASE_URL=http://127.0.0.1:8765/ python scripts/check_browser.py
```

The check validates HTML parsing, local links and fragments, bilingual attributes, canonical URLs, JSON-LD, external-link safety attributes and sitemap entries.

## After publishing

Run:

```bash
python scripts/check_live_portfolio.py
```

It checks the deployed portal, portfolio, case studies, technical notes and their CSS/JavaScript assets. The scheduled GitHub Actions smoke test repeats this check.

## Rollback

Do not delete files or force-push to roll back a release. Identify the offending commit and create a normal revert:

```bash
git revert <commit-sha>
git push origin HEAD:main
```

The manual `restore-index.yml` workflow restores a historical copy of `index.html`; it is not a general rollback mechanism and requires the exact confirmation input described in the workflow.

## Telegram archive

The active workflow is `.github/workflows/update-telegram-posts.yml`. It uses `requirements-telegram.txt` with hash-locked dependencies. The root-level `telegram-posts.yml` and `post-channels/channels-posts.yml` are retained reference files; GitHub does not execute them from their current locations.
