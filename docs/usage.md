# Usage

Current status: prototype scripts.

The repository is not yet a polished CLI package. The workflow is currently script-based.

## Setup

From the repository root:

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt
python -m playwright install chromium

## Workflow

Phase 0.7:
python scripts/phase0_7_destination_posts.py

Phase 0.8:
python scripts/phase0_8_opportunity_matrix.py

Phase 0.9:
python scripts/phase0_9_product_offer.py

## Output policy

Generated outputs should remain outside Git.

Do not commit real crawl outputs, screenshots, ZIPs, logs, virtual environments or private client data.
