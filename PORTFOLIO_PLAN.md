# SiNAVM — Portfolio & Portal Evolution

## Product decision

- Keep the existing root website as the Internet Tools Portal.
- Build the developer portfolio independently under `portfolio/`.
- Support Persian (default, RTL) and English (LTR).
- Use a modern, minimal, professional visual language.
- Preserve existing service routes, Telegram publishing, downloads, legal pages and current workflows unless a separately reviewed change is approved.

## Phase 1 — Identity and information architecture

- [x] Define the two distinct audience journeys: developer portfolio and Internet Tools Portal.
- [x] Create an independent bilingual portfolio entry point.
- [x] Establish a concise developer positioning statement.
- [x] Add selected project descriptions and links.
- [x] Update the repository README to explain both experiences.
- [ ] Add a discoverable link from the existing portal homepage after reviewing its DOM and automated patch workflows.
- [ ] Verify all project descriptions and external destinations with the owner.

## Phase 2 — Visual system and project storytelling

- [ ] Review desktop and mobile rendering.
- [ ] Add dedicated case-study pages for SVM and IR Net Atlas.
- [ ] Add architecture diagrams and carefully sourced project metrics.
- [ ] Improve navigation, accessibility and language persistence.
- [ ] Add a resume page only after owner-approved career details are supplied.

## Phase 3 — Technical structure

- [ ] Split reusable CSS and JavaScript into versioned assets where this does not conflict with existing automation.
- [ ] Add HTML validation and link checks.
- [ ] Establish a lightweight test workflow for portfolio pages.
- [ ] Review canonical URLs, sitemap and structured metadata.

## Phase 4 — Security and operations

- [ ] Audit GitHub Actions permissions and token scope.
- [ ] Pin third-party Actions to verified full commit SHAs.
- [ ] Pin Python dependencies.
- [ ] Review Telegram archive publication rules and sensitive-data handling.
- [ ] Remove or document obsolete workflows and scripts after confirming dependencies.

## Phase 5 — Credibility and ongoing publishing

- [ ] Publish technical articles with reproducible details.
- [ ] Add only verifiable project metrics with sources and update dates.
- [ ] Document project ownership and contribution boundaries.
- [ ] Add contact and collaboration guidance.

## Safety and rollout

All changes are developed on a feature branch and proposed through a pull request. The existing `main` branch and root portal remain unchanged until review and explicit merge approval.
