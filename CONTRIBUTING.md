# Contributing

This repository is currently private and proprietary.

## Development principles

- Keep real audit outputs out of Git.
- Prefer small, reviewable changes.
- Keep site-specific settings in config files, not hardcoded into reusable logic.
- Add tests before broad refactors.
- Do not claim revenue uplift without measurement.

## Before committing

Run:

```bash
./scripts/verify_repo_safe.sh
```

The verifier checks for forbidden tracked files, example sanitization and Python syntax.

## Branch naming

Recommended prefixes:

- `hardening/`
- `config/`
- `docs/`
- `tests/`
- `refactor/`

## Output policy

Generated outputs belong in `outputs/` or outside the repository and must remain untracked.
