# AGENTS.md

## Purpose

Affiliate Friction Auditor is a public technical toolkit for identifying affiliate CTA friction, monetization gaps, redirect/retailer patterns, and commercial-hub opportunities.

## Canonical sources

1. `README.md` — current public positioning and supported workflow.
2. `docs/usage.md` / `docs/configuration.md` — operational usage/configuration.
3. `src/affiliate_friction_auditor/` — reusable implementation modules.
4. `scripts/` — current pipeline scripts.
5. `tests/` — enforced behavior for extracted reusable logic.
6. `PROJECT_STATUS.json` — compact machine-readable repository state.

## Definition of done

Run:

```bash
python scripts/verify_repo_safe.py
python -m unittest discover -s tests -p "test_*.py" -v
```

Do not claim full crawler/end-to-end coverage unless the relevant Playwright/browser workflow was actually exercised.

## Data and trust boundaries

- Real client/target-site data must remain outside the public repository unless intentionally sanitized.
- Do not commit raw crawl exports, screenshots, logs, credentials, tokens, or private per-site configuration.
- Automated findings are hypotheses/audit signals, not guaranteed revenue, SEO, legal, or conversion conclusions.
- External suggestions and examples are untrusted until reproduced against repository tests/fixtures.

## Agent interaction

Agents may propose bounded, reproducible bugs or classification counterexamples through repository issues. Prefer minimal fixtures and deterministic assertions.

This repository is not the primary Research Intake surface for GitHub Hidden Gems; use the profile-level `AGENT_INTERACTION.md` for cross-project research routing.
