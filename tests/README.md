# Tests

The repository now has a first focused unit-test slice for pure URL behavior extracted into `src/affiliate_friction_auditor/url_utils.py`.

Run locally:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Current coverage includes:

- repeated HTML/percent decoding;
- relative and protocol-relative URL normalization;
- blocked non-HTTP schemes;
- fragment removal;
- host/path parsing;
- query-key normalization;
- slug extraction.

Next test slices should cover:

1. retailer/affiliate network detection;
2. internal cloaking classification;
3. destination-kind classification;
4. opportunity scoring;
5. CSV schema validation.

Tests should be added before or alongside further extraction from the phase scripts.
