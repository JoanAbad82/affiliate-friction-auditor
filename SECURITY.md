# Security Policy

## Supported status

Affiliate Friction Auditor is a public early-stage toolkit. The latest code on the default branch is the current development surface unless a release explicitly states otherwise.

## Reporting a security issue

Do not open public issues containing sensitive data, client URLs, crawler outputs, tokens, credentials, screenshots, or private audit results.

Report sensitive security concerns privately to the repository owner. Public issues are appropriate only when they can be reproduced without exposing confidential material.

## Sensitive data policy

Do not commit:

- real client audit outputs;
- raw crawl exports;
- screenshots;
- ZIP archives;
- logs;
- virtual environments;
- `.env` files;
- API tokens or credentials;
- private per-site configuration.

Synthetic or deliberately sanitized examples are allowed.

## Crawler safety

The current workflow performs browser-assisted auditing. Before using it on a website:

- confirm the audit scope is authorized;
- keep crawl volume reasonable;
- respect applicable site policies and technical limits;
- avoid collecting unnecessary personal or confidential data.

## Output limitations

Automated findings require manual review. The toolkit does not guarantee:

- affiliate-program compliance;
- advertising-disclosure compliance;
- legal compliance;
- revenue uplift;
- conversion improvement;
- SEO performance;
- merchant approval.

## Dependency and code safety

The repository currently uses Playwright as a runtime dependency. Review dependency changes before merging and avoid executing untrusted code from audited sites.
