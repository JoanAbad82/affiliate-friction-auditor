# Contributing

Affiliate Friction Auditor is public software licensed under Apache-2.0.

## Development principles

- Keep real audit outputs and private target-site data out of Git.
- Prefer small, reviewable changes.
- Keep site-specific settings in config files, not hardcoded into reusable logic.
- Add or update tests when extracting reusable behavior.
- Do not claim revenue uplift or compliance outcomes without evidence.
- Preserve conservative handling of uncertain affiliate signals.

## Before committing

Run the cross-platform repository verifier:

```bash
python scripts/verify_repo_safe.py
```

The verifier checks:

- forbidden tracked files;
- example sanitization;
- Python syntax for the current source/scripts.

GitHub Actions runs the same validation on pushes and pull requests.

## Branch naming

Recommended prefixes:

- `hardening/`
- `config/`
- `docs/`
- `tests/`
- `refactor/`

## Output policy

Generated outputs belong in `outputs/` or outside the repository and must remain untracked.

## Scope

Large behavior changes should be separated from public-presentation, licensing, or repository-hardening changes whenever practical.
