---
applyTo: "scripts/**,src/**"
---

For implementation/refactor work:
- prefer small pure functions with explicit inputs;
- preserve existing wrapper/function contracts when extracting shared logic;
- keep network/browser behavior separate from pure classification helpers;
- do not move private target configuration into public source;
- add tests for ambiguous, malformed, and adversarial URLs/classification cases.
