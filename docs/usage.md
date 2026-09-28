# Usage

Current status: public script-based toolkit.

The repository is not yet a polished CLI package. The workflow is currently implemented through the phase scripts.

## Setup

From the repository root:

```bash
python -m venv .venv
# activate the virtual environment for your platform
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Workflow

Phase 0.7:

```bash
python scripts/phase0_7_destination_posts.py --config configs/example_affiliate_site.json
```

Phase 0.8:

```bash
python scripts/phase0_8_opportunity_matrix.py --config configs/example_affiliate_site.json --input /path/to/phase0_7_output
```

Phase 0.9:

```bash
python scripts/phase0_9_product_offer.py --config configs/example_affiliate_site.json --input /path/to/phase0_8_output
```

See [configuration.md](configuration.md) for configuration precedence and supported keys.

## Repository validation

Run:

```bash
python scripts/verify_repo_safe.py
```

This check is intentionally cross-platform and is also executed by GitHub Actions.

## Output policy

Generated outputs should remain outside Git.

Do not commit real crawl outputs, screenshots, ZIPs, logs, virtual environments, private per-site configs, or client data.
