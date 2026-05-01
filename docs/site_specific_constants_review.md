# Site-specific constants review

Generated during phase 1.2A. Updated during phase 1.2B.

Goal: identify values that should move from prototype scripts into configuration files.

## Phase 1.2B status

Resolved:

- Main hardcoded prototype site defaults in phases 0.7, 0.8, and 0.9 now use public-safe example values.
- `scripts/_site_config.py` supports `--config` and `AFA_SITE_CONFIG`.
- Phase 0.8 and 0.9 support `--input` while keeping positional input compatibility.
- `configs/example_affiliate_site.json` includes all supported public-safe keys.
- Real per-site configs should remain private and untracked unless explicitly approved.

## Configurable values

- `SITE_LABEL`
- `ROOT_HOST`
- `EXPECTED_AMAZON_DOMAIN`
- `HUB_URLS`
- `MAX_DESTINATIONS_PER_HUB`
- `MAX_TOTAL_DESTINATIONS`
- `OUTPUT_SLUG`
- `PHASE07_PREFIX`
- `PHASE08_PREFIX`
- `PHASE09_PREFIX`

## Remaining site-specific strings

Spanish commercial heuristic terms, retailer names, and marketplace checks remain in scripts because they are scoring and classification logic rather than target-site configuration.
