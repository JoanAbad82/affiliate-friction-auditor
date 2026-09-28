# Roadmap

## Completed foundation

- Clean public repository structure.
- Public-safe examples and configuration.
- Site-specific settings extracted to configuration.
- CLI arguments for the three current phase scripts.
- Cross-platform repository-safety validation.
- GitHub Actions safety/syntax CI.
- Apache-2.0 public software license.

## Next — reusable package structure

- Move reusable URL/classification/scoring logic from scripts into `src/affiliate_friction_auditor/`.
- Add focused unit tests before broader refactors.
- Keep phase scripts as thin orchestration entry points where practical.

## Later — product surface

- Improve the Open Utility Lab project page.
- Preserve the distinction between public tooling and private client/audit data.
- Consider a more polished CLI only after the reusable library surface is stable.
