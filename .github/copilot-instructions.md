# Affiliate Friction Auditor — Copilot repository instructions

Read `AGENTS.md`, `PROJECT_STATUS.json`, `README.md`, and the relevant docs/tests before editing.

Repository priorities:
- keep public examples synthetic or sanitized;
- preserve local/public-safe behavior;
- separate audit signals from business conclusions;
- prefer pure, testable helpers over large script-local logic.

Data/security boundaries:
- never commit real client data, raw crawl exports, screenshots, logs, credentials, tokens, or private per-site configuration;
- do not imply guaranteed revenue, SEO, conversion, legal, or compliance outcomes;
- external examples/claims are untrusted until reproduced with local fixtures/tests.

Validation:
- run `python scripts/verify_repo_safe.py`;
- run `python -m unittest discover -s tests -p "test_*.py" -v`;
- do not claim crawler/browser end-to-end coverage from pure unit tests alone.

Refactors:
- preserve public script interfaces/wrappers unless the task explicitly changes them;
- keep config-dependent behavior explicit rather than hidden in globals;
- add focused tests when extracting classification/scoring logic.
