# GitHub private setup

Recommended initial setup:

1. Create a new GitHub repository named affiliate-friction-auditor.
2. Set visibility to Private.
3. Do not initialize with README, license or gitignore.
4. Add the remote locally.
5. Push branch main.

SSH remote example:
cd "$HOME/affiliate-friction-auditor"
git remote add origin git@github.com:YOUR_USER_OR_ORG/affiliate-friction-auditor.git
git push -u origin main

HTTPS remote example:
cd "$HOME/affiliate-friction-auditor"
git remote add origin https://github.com/YOUR_USER_OR_ORG/affiliate-friction-auditor.git
git push -u origin main

Keep this repository private until site-specific constants are moved to config files and public-safe demo data exists.
