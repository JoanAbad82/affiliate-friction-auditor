# Configuration

The phase scripts use public-safe defaults and can be pointed at a site config with `--config` or the `AFA_SITE_CONFIG` environment variable.

## Demo config

`configs/example_affiliate_site.json` is public-safe and does not contain real client data.

## CLI usage

Run phase 0.7 with an explicit config:

```bash
python scripts/phase0_7_destination_posts.py --config configs/example_affiliate_site.json
```

Run phase 0.8 with a config and a specific phase 0.7 output folder or ZIP:

```bash
python scripts/phase0_8_opportunity_matrix.py --config configs/example_affiliate_site.json --input /path/to/phase0_7_output
```

Run phase 0.9 with a config and a specific phase 0.8 output folder or ZIP:

```bash
python scripts/phase0_9_product_offer.py --config configs/example_affiliate_site.json --input /path/to/phase0_8_output
```

For phases 0.8 and 0.9, `--input` is optional. If omitted, the scripts keep their discovery behavior and search common local folders for the latest matching output.

## Environment variable

Use `AFA_SITE_CONFIG` when you want the same private config to apply without passing `--config` every time:

```bash
export AFA_SITE_CONFIG=/path/to/private_site_config.json
python scripts/phase0_7_destination_posts.py
python scripts/phase0_8_opportunity_matrix.py --input /path/to/phase0_7_output
python scripts/phase0_9_product_offer.py --input /path/to/phase0_8_output
```

An explicit `--config` value takes precedence over `AFA_SITE_CONFIG`.

## Supported config keys

- `site_label`
- `root_host`
- `expected_amazon_domain`
- `output_slug`
- `hub_urls`
- `max_destinations_per_hub`
- `max_total_destinations`
- `phase07_prefix`
- `phase08_prefix`
- `phase09_prefix`

If `output_slug` is set and a phase prefix is omitted, the scripts derive prefixes like `affiliate_phase0_8_<output_slug>_`.

## Policy

Real per-site configs should remain private and untracked unless they are intentionally public-safe and explicitly approved for commit.
