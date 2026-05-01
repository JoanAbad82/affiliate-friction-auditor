# Configuration

The current scripts still contain some prototype defaults, but project settings should progressively move into JSON configuration files under `configs/`.

## Demo config

`configs/example_affiliate_site.json` is public-safe and does not contain real client data.

## Recommended future CLI

Target shape:

```bash
python scripts/phase0_7_destination_posts.py --config configs/example_affiliate_site.json
python scripts/phase0_8_opportunity_matrix.py --input outputs/phase0_7
python scripts/phase0_9_product_offer.py --input outputs/phase0_8
```

## Site-specific values to move out of scripts

- `SITE_LABEL`
- `ROOT_HOST`
- `EXPECTED_AMAZON_DOMAIN`
- `HUB_URLS`
- output folder prefixes
- per-site limits

## Policy

Do not commit real client configs unless they are intentionally public-safe and approved.
