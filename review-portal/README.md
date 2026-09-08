# Sami domain review portal

Architecture: GitHub Pages -> HTTPS POST -> Cloudflare Worker -> GitHub Issue.
Plain HTML, CSS and JavaScript; no third-party browser scripts or analytics.
Email is not the primary store because the structured Issue preserves a complete,
inspectable submission in a private evidence repository. An Issue is incoming human evidence,
not adjudication, a G5 gate pass, clinical validation or SPICT approval. A later
explicitly controlled importer must determine incorporation into G5 records.
The Worker never commits or changes disposition files.

Frozen review candidate: `6a1a270a9d41953000b401256af0d58f7a3c0576`.
This constant must never be replaced with a portal implementation commit.
Run: `G5-20260908-001`. Units: 017, 021, 025, 026, 045, 049 (S4A-2026 prefix).

## Controlled G5 reviewer activation

See PUBLICATION_STATUS.md. Controlled G5 reviewer portal activation is configured;
the production Worker is DEPLOYED, as reported by the Project Owner, at
https://spict-sami-review.mmvirta75.workers.dev/submit
(version 4513d228-89c9-4a3a-b1b1-8f9e7108e172).
The GitHub Pages frontend is NOT YET DEPLOYED; default-branch workflow bootstrap
is still required as described below.
this is NOT SPICT approval, NOT clinical validation and NOT final publication.
The six-item candidate remains frozen at the SHA above. Submission requires
REVIEW_ACCESS_CODE; incoming GitHub Issues are evidence only, not adjudication.
This work package performs no deployment or Issue creation. Pages is public,
including its JSON data; the submission code does not protect page reading.
The evidence repository MUST be PRIVATE before activation. The Worker verifies
its privacy through the GitHub repository API before each Issue creation. Missing,
public, mismatched or unverifiable repositories fail closed; no Issue is created. No permission, deployment, or review is implied here.

## Reproduce and preview

From the repository root, using the project's Python 3.12+ environment:

```powershell
.venv\Scripts\python scripts/build_sami_review_portal.py
.venv\Scripts\python scripts/validate_sami_review_portal.py
.\tools.ps1 -Task Test
.\tools.ps1 -Task Lint
.\tools.ps1 -Task TypeCheck
npm --prefix review-portal/worker test
.venv\Scripts\python -m http.server 8000 --bind 127.0.0.1 --directory review-portal/site
```

Open `http://127.0.0.1:8000/review/sami/`. No secret is needed for UI preview.
The runtime now points to the production endpoint. Do not submit during a local
UI preview; production CORS accepts only https://foxrav.github.io.
The builder reads frozen Git blobs and refuses live evidence drift. Deterministic
JSON uses UTF-8, sorted keys, two-space indentation, LF, and a trailing newline.
The SHA-256 covers the exact review-data.json bytes. Metadata is separate to avoid
a self-referential hash. Source SHA-256 remains mapped by unit in Worker config and
is copied into normalized submission evidence. Public unit JSON uses an exact
field whitelist and excludes critic alternatives.

## Configuration and deployment reference (no deployment in this work package)

### Local development secret handling

Local development secrets go in `review-portal/worker/.dev.vars`.
Names only (the ellipses below are placeholders, not values):

```dotenv
GITHUB_TOKEN="..."
REVIEW_ACCESS_CODE="..."
```

`.dev.vars` is local only: never commit it or any `.dev.vars.*` variant.
Never paste a PAT into source files. Local `wrangler dev` may load this file;
this does not deploy the Worker. No local secrets file is supplied by this project.
The `[secrets] required` declaration lists only the two required secret names.
Controlled reviewer use is configured with `PUBLICATION_AUTHORIZED = "true"`
and `workers_dev = true`; secret values are not included in configuration.
Validation checks ignore behavior and rejects tracked local secret files without
reading their contents; ignored local secret values are excluded from file scans.

Required Worker secrets: `GITHUB_TOKEN`, `REVIEW_ACCESS_CODE`. Set them with
`npx wrangler secret put GITHUB_TOKEN` and `npx wrangler secret put REVIEW_ACCESS_CODE`
from review-portal/worker, entering values interactively. Never put secrets in
files, command arguments, URLs, frontend config, logs, or Issues. Use a fine-grained
GitHub PAT restricted only to the configured PRIVATE repository
FoxRav/SPICT-4ALL-FI-2026-review-evidence, with **Issues: Read and write**
(and GitHub's implicit metadata read permission). No broader permission is needed.
The production access code must be cryptographically random, 24–256 characters,
and shared with Sami separately; rotate it after the review. The Worker fails
closed if the configured secret falls outside that range. No actual code is included.

Nonsecret Worker vars: `ALLOWED_ORIGIN` (production `https://foxrav.github.io`),
`GITHUB_EVIDENCE_REPOSITORY` (configured value
`FoxRav/SPICT-4ALL-FI-2026-review-evidence`), `PUBLICATION_AUTHORIZED`
(exact `true` for controlled G5 reviewer use). `workers_dev` is `true` and
`preview_urls` is `false` and is deployed.
Origin matching is exact; wildcard is refused. For local Worker integration use a
separate local environment and localhost origin, never production credentials.
Wrangler observability is disabled; our code does not collect IPs or log payloads.
Hosting providers may maintain their own service logs independently.

For a separately authorized deployment: install an approved Wrangler version,
authenticate to the correct Cloudflare account, provision secrets and deploy with
`npx wrangler deploy`. workers.dev is already enabled in configuration.
runtime-config.js `workerSubmitUrl` is already set to the exact production endpoint:
https://spict-sami-review.mmvirta75.workers.dev/submit
The validator requires that HTTPS host and `/submit` path with no credentials,
query or fragment. No token or access code belongs in config.

DEFAULT_BRANCH_WORKFLOW_BOOTSTRAP_REQUIRED

GitHub workflow_dispatch requires the workflow file to exist on the default branch.
After source-publication permission is confirmed, the reviewed inert Pages workflow
must first exist on default branch main through a separately authorized change.
Do not modify main now. Only after that bootstrap may the workflow be manually
dispatched against the explicitly approved portal branch/ref (currently
g5-human-adjudication). Select GitHub Actions in repository Settings > Pages and set
repository variable `SPICT_REVIEW_PORTAL_PUBLICATION_AUTHORIZED` to exact `true`,
review the branch and site-only artifact, and manually dispatch pages-review.yml
from g5-human-adjudication. The workflow fails before upload if the variable is
absent/false or the branch is wrong. It never runs on push. A project Pages URL
includes the repository prefix before `/review/sami/`; all assets use relative URLs.
Do not trigger this workflow as part of this build.

## Submission semantics

Schema 1.0 accepts exactly the six IDs and three decision enums. The server trims
reviewer strings, edited text and rationales; sorts decisions in canonical unit
order; supplies the frozen current text for ACCEPT_CURRENT and further-review
decisions; and adds source hashes and a server ISO UTC timestamp. It serializes
objects recursively with sorted keys and compact JSON (arrays preserve order),
then SHA-256 hashes the UTF-8 bytes before adding submission_id. Access codes,
unknown fields and response values are excluded. The Issue's JSON block contains
this normalized evidence plus its ID. Requests are limited to 64 KiB; names to
120 characters, roles to 240, corrections to 2000 and rationales to 1200. Limits
use JavaScript UTF-16 code units consistently in browser and Worker. The complete
final duplicated Issue body is encoded as UTF-8 and capped at 60000 bytes; larger
bodies return HTTP 413 in Finnish before any GitHub API call.

One validated request first checks repository privacy through the GitHub metadata
API, then performs one Issue creation call. Privacy/API errors and tokens are never
returned to the client. The success UI shows confirmation and submission ID only;
Sami does not need GitHub access. No private Issue URL is returned. The browser blocks duplicate
clicks while pending. There is no persistent idempotency store: a later resubmission
is a separate timestamped record. After a timeout/502 the reviewer must ask the
maintainer to check Issues before retrying, since creation may have succeeded.
The access code is retained only in request memory and cleared from the field after
an attempt. Only decision drafts are stored in localStorage, keyed by candidate and
data hash; reviewer identity, confirmation and access code are not persisted.
Browser storage failure is reported. Clear-draft and successful submission remove
the draft. On a shared browser, clear drafts when finished.

Tests mock GitHub and create no real Issues. Future G6 can reuse the UI/validation
patterns with a separately frozen dataset, schema/run, authority and permission
review; this implementation does not start G6 or adjudicate any unit.

## Verified Action pins

Verified with git ls-remote against the official actions repositories on 2026-09-08:

| Action | Release tag | Commit |
| --- | --- | --- |
| actions/checkout | v4.2.2 | 11bd71901bbe5b1630ceea73d27597364c9af683 |
| actions/setup-python | v5.6.0 | a26af69be951a213d495a4c3e4e4022e16d87065 |
| actions/upload-pages-artifact | v3.0.1 | 56afc609e74202658d3ffba0e8f6dda462b719fa |
| actions/deploy-pages | v4.0.5 | d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e |

No evidence repository has been created as part of this work.
