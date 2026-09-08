PUBLICATION_STATUS: CONTROLLED_G5_REVIEWER_ACTIVATION_CONFIGURED

Controlled G5 reviewer portal activation is configured with workers_dev = true
and PUBLICATION_AUTHORIZED = "true". This work package performs no deployment.
Production Worker: DEPLOYED (Project Owner reported).
Worker version: 4513d228-89c9-4a3a-b1b1-8f9e7108e172
Endpoint: https://spict-sami-review.mmvirta75.workers.dev/submit
GitHub Pages frontend: NOT YET DEPLOYED.
preview_urls = false is deployed.
This is NOT SPICT approval, NOT clinical validation and NOT final publication.
The six-item domain-review candidate remains frozen at:
6a1a270a9d41953000b401256af0d58f7a3c0576
Submission requires REVIEW_ACCESS_CODE. Incoming GitHub Issues are evidence only,
not adjudication. G5 remains IN PROGRESS.

DEFAULT_BRANCH_WORKFLOW_BOOTSTRAP_REQUIRED

After source-publication permission confirmation, the reviewed inert Pages workflow
must first exist on default branch main. Only then may workflow_dispatch target
the explicitly approved portal branch/ref. Main is not modified by this work.
SPICT_REVIEW_PORTAL_PUBLICATION_AUTHORIZED must still equal exact true; only the
site artifact may be deployed, and no push-triggered deployment is allowed.

Configured evidence repository: FoxRav/SPICT-4ALL-FI-2026-review-evidence.
The Worker must verify it is PRIVATE before every Issue creation.
The frontend runtime URL is configured to the production endpoint above.
No secret values or Pages workflow are changed by this work package.
