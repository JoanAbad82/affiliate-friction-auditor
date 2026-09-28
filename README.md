# Affiliate Friction Auditor

Public audit toolkit for identifying affiliate CTA friction, monetization gaps, and commercial hub opportunities.

**Live project page:** https://openutilitylab.com/affiliate-friction-auditor/

Affiliate Friction Auditor analyzes commercial hub/listing structures where users may need to open a destination post before reaching a monetized offer. The repository exposes the technical workflow, public-safe configuration, synthetic examples, and reproducible audit logic.

## Current status

The project is an **early public technical toolkit**, not a finished SaaS or polished CLI package.

The current workflow is script-based:

1. validate destination posts;
2. build a hub-to-destination opportunity matrix;
3. generate a structured product/audit proposal from the findings.

Manual review remains important. Automated findings can be wrong, and outputs must not be presented as guaranteed revenue, SEO, compliance, or conversion outcomes.

## Core idea

Many affiliate websites already monetize destination posts, but their hub or listing pages can add unnecessary friction:

```text
hub/listing page -> destination post -> affiliate CTA
```

The toolkit looks for cases where the commercial path can be made clearer or more direct.

## What it produces

- hub-to-destination opportunity matrix;
- detection of monetized destination posts;
- detection of probable affiliate gaps;
- prioritized implementation backlog;
- ROI scenario templates;
- structured audit/proposal assets.

## Public-safe workflow

Real client or target-site material must remain outside the repository unless it is intentionally sanitized and approved for publication.

Do not commit:

- real client audit outputs;
- raw crawl exports;
- screenshots;
- ZIP archives;
- logs;
- credentials or tokens;
- private per-site configuration.

The committed examples are reduced or synthetic and exist only to demonstrate output structure.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
# activate the environment for your platform
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

See [docs/usage.md](docs/usage.md) and [docs/configuration.md](docs/configuration.md) for the current script workflow.

## Repository safety validation

The cross-platform safety check validates tracked-file policy, public-safe examples, and Python syntax:

```bash
python scripts/verify_repo_safe.py
```

GitHub Actions runs this validation on pushes and pull requests.

## Product positioning

This is not generic SEO. It is a focused affiliate-friction audit workflow for commercial hubs and listing pages.

The repository is public software under the **Apache License 2.0**. Public source access does not imply access to private client data, private configurations, or unpublished commercial work.

## Tests and roadmap

The first reusable URL utilities now live in `src/affiliate_friction_auditor/url_utils.py` with focused unit tests. The next engineering slices will extract retailer/redirect classification, internal-cloak classification, destination-kind logic, and opportunity scoring.

Run the current tests with:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

See [docs/roadmap.md](docs/roadmap.md).

## Security and responsible use

Only audit websites and data you are authorized to review. Keep crawl volume reasonable and manually review findings before acting on them.

See [SECURITY.md](SECURITY.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
