# Roadmap

## Completed foundation

- Clean public repository structure.
- Public-safe examples and configuration.
- Site-specific settings extracted to configuration.
- CLI arguments for the three current phase scripts.
- Cross-platform repository-safety validation.
- GitHub Actions safety/syntax CI.
- Apache-2.0 public software license.

## Reusable package structure — in progress

Completed first slice:

- extracted pure URL helpers into `src/affiliate_friction_auditor/url_utils.py`;
- retained compatibility wrappers in the phase scripts;
- added focused cross-platform unit tests.

Next slices:

- extract retailer/redirect classification;
- extract internal-cloak classification;
- extract destination-kind and opportunity-scoring logic;
- keep phase scripts as thin orchestration entry points where practical.

## Later — product surface

- Improve the Open Utility Lab project page.
- Preserve the distinction between public tooling and private client/audit data.
- Consider a more polished CLI only after the reusable library surface is stable.
