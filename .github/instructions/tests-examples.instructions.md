---
applyTo: "tests/**,examples/**"
---

For tests/examples:
- use synthetic or sanitized data only;
- avoid real client domains, private markers, secrets, and raw crawl output;
- prefer deterministic assertions with no network access;
- document when coverage is unit-only and does not exercise Playwright/browser flows.
