# Affiliate Friction Auditor — Project Retrospective

**Classification (October 2026):** Early AI-assisted engineering work; functional reference implementation. **Commercial priority:** withdrawn. **Availability:** public code and free local demonstration remain available.

## Origin and purpose

I started Affiliate Friction Auditor relatively early in my experience with AI-assisted development. The aim was to turn an observable, limited problem into a working tool: inspect supplied HTML for affiliate links, commercial calls to action, redirect patterns, and structural friction that might warrant human review.

The project evolved into a public, inspectable implementation with deterministic checks, structured findings, a browser-side demonstration that processes supplied HTML locally, synthetic examples, and repository validation. It provided valuable experience in scoping, implementation, documentation, privacy boundaries, and testing.

## What the project demonstrates — and what it does not

The tool can highlight patterns in the supplied HTML. Its output is an indicative first-pass assessment, not a measured conversion loss, revenue forecast, complete JavaScript-rendered crawl, or proof that any proposed change will improve outcomes. The public examples are synthetic or sanitized, not client success evidence.

These limitations have always mattered; retaining reproducible, explainable analysis is still useful.

## Why the commercial priority changed

The available capabilities of general-purpose AI-assisted analysis have expanded since the project's early development. They can often provide broader contextual interpretation than a narrowly scoped rule-based HTML analyzer. This changes the commercial hypothesis for a standalone audit product.

**This is an assessment of strategic fit, not a benchmark finding.** No controlled comparison has established that AI tools are universally more accurate, that this auditor is obsolete, or that deterministic analysis has no market. Nor has the project demonstrated sufficient demand, a defensible paid differentiator, or verified client outcomes to justify prioritizing commercialization.

The decision is therefore to **stop treating Affiliate Friction Auditor as a commercial priority**. The free demonstration remains accessible as a reference; no paid audit service or feature roadmap is being offered through this project.

## What remains valuable

- A bounded example of converting an idea into functioning, inspectable software.
- Deterministic local analysis and machine-readable output, with stated limits.
- Lessons in user-facing clarity, security boundaries, validation, and scope control.
- A transparent record of updating product decisions as technology and evidence change.

The project stays public rather than being deleted or technically archived. Its existing history, tests, and reproducibility artifacts remain intact. That does not imply a commitment to active feature development or an end to necessary safety maintenance.

## Conditions for reconsideration

Reopening investment would require credible evidence of a specific user problem, a repeatable advantage over available alternatives, measurable delivery cost, and demand or collaborator interest. Until those conditions are met, the repository is a **reference implementation and professional learning record**, not an active commercial offer.

For operational instructions and current test boundaries, consult the [README](../README.md), [usage guide](usage.md), and repository tests.
