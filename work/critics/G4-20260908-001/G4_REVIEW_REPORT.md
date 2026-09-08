# SPICT-4ALL FI — G4 independent critic consolidation

Work package: **WP-G4-CONSOLIDATION-AUDIT-001**
Run: **G4-20260908-001**
Role: **G4 critic consolidation**
Status: **INDEPENDENT_CRITICS_COMPLETE_AWAITING_G5**
Coverage: **54/54**

G4 does not adjudicate translation units and does not revise Finnish wording.
This package consolidates two completed independent critic outputs.
It is not human approval and not clinical validation. These mechanical checks
are not clinical validation.

G5 was not created. No Finnish G2 candidate was changed. No G3 back-translation
was changed. No critic output was changed.

## Critic coverage

- Review input: **54/54**
- Critic A: **54/54**
- Critic B: **54/54**
- Combined findings: **54/54**
- Same unit IDs and original order across review input, Critic A, Critic B,
  G2 candidates, and G3 back-translation.

## Critic independence statement

Critic A and Critic B were run independently. Neither critic saw the other critic's findings. This consolidation does not alter either critic output, does not reconcile proposed Finnish wording into a new candidate, and is not human adjudication.

## Model provenance

### Critic A

- **actual model:** NOT_INDEPENDENTLY_RECORDED
- No operator-stated actual model for Critic A is recorded in WP-G4-CONSOLIDATION-AUDIT-001. This package does not infer Critic A's model from config/model_roles.yaml or from critic prompt files.

### Critic B

- **actual model:** Cursor Grok 4.6
- Recorded from the operator Critic B review prompt for G4-20260908-001 (ACTUAL MODEL: Cursor Grok 4.6). No independent API request log is packaged.

### Same-family limitation

G2 synthesis actual model: **Cursor Grok 4.6**.

Critic B and G2 synthesis both used Cursor Grok 4.6. This same-family limitation does not invalidate Critic B. Independent cross-family review evidence cannot be claimed from Critic A in this package because Critic A's actual model is not independently recorded.

Configured / planned adversarial-critic role model in `config/model_roles.yaml`:
Cursor Grok 4.6 Medium. This consolidation does not treat that configured role
as Critic A's recorded actual model.

## Raw severity distributions

### Critic A

- records: **54**
- ISSUE: **7**
- NONE: **47**
- LOW: **3**
- MEDIUM: **2**
- HIGH: **1**
- BLOCKER: **1**

### Critic B

- records: **54**
- ISSUE: **21**
- NONE: **33**
- LOW: **12**
- MEDIUM: **7**
- HIGH: **2**
- BLOCKER: **0**

## Cross-critic result

Expected and observed:

- corroborated by both critics: 7
- Critic-A-only issues: 0
- Critic-B-only issues: 14

Corroboration is stronger review evidence requiring later adjudication. It is
not human approval and not automatic proof of error.

## 7 corroborated findings

- `S4A-2026-001`
- `S4A-2026-009`
- `S4A-2026-025`
- `S4A-2026-026`
- `S4A-2026-042`
- `S4A-2026-045`
- `S4A-2026-049`

## 14 Critic-B-only findings

- `S4A-2026-000`
- `S4A-2026-003`
- `S4A-2026-004`
- `S4A-2026-008`
- `S4A-2026-014`
- `S4A-2026-017`
- `S4A-2026-018`
- `S4A-2026-021`
- `S4A-2026-033`
- `S4A-2026-034`
- `S4A-2026-036`
- `S4A-2026-040`
- `S4A-2026-043`
- `S4A-2026-047`

Observed Critic-A-only findings: **0**.

Critic-B-only MEDIUM findings:

- `S4A-2026-008`
- `S4A-2026-017`
- `S4A-2026-021`
- `S4A-2026-036`

## Strongest corroborated findings

These are high-priority G5 adjudication items. This consolidation does not
automatically accept a correction.

### S4A-2026-025

- Critic A: **HIGH**
- Critic B: **HIGH**
- finding_status: **CORROBORATED**
- combined_review_priority: **HIGH**

Both critics independently flagged a literal Finnish rendering of
"when the chest is at its best".

### S4A-2026-045

- Critic A: **BLOCKER**
- Critic B: **HIGH**
- finding_status: **CORROBORATED**
- combined_review_priority: **BLOCKER**

Both critics independently flagged a literal Finnish rendering of
"chest infections". Critic A recorded BLOCKER; Critic B recorded HIGH.
This consolidation does not reinterpret or downgrade that disagreement.

## MEDIUM-or-higher findings from either critic

Units with Critic A or Critic B severity MEDIUM, HIGH, or BLOCKER:

- `S4A-2026-001`
- `S4A-2026-008`
- `S4A-2026-009`
- `S4A-2026-017`
- `S4A-2026-021`
- `S4A-2026-025`
- `S4A-2026-026`
- `S4A-2026-036`
- `S4A-2026-042`
- `S4A-2026-045`
- `S4A-2026-049`

`combined_review_priority` is the maximum reported critic severity for triage
only. Disagreement is not downgraded. No consensus wording is invented.

## Human-decision conflicts

Preserve explicitly that critic findings concerning `S4A-2026-001` and
`S4A-2026-042` intersect the recorded Project Owner wording decision for
"less well" (`terveydentila on heikentynyt`).

Preserve explicitly that `S4A-2026-017` intersects the recorded Project Owner
wording for "not well enough for cancer treatment"
(`ei ole riittävän hyväkuntoinen syöpähoitoon`).

Those three units are recorded as:

`EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5`

The recorded human decisions are **not** overridden. The critic findings are
**not** suppressed.

`S4A-2026-021` frailty/hauraus has **no final recorded human wording
decision**. That distinction is preserved. Critic B flagged it independently;
Critic A did not.

## Unresolved source-authority issues

Source-authority issues are kept separate from translation critic findings.
Critic severity is not a source-authority BLOCKER.

### S4A-2026-000

- source-authority status remains **UNRESOLVED**
- not eligible for document insertion
- publication-blocking
- critic findings do not resolve this

### S4A-REQ-2026-001

- remains **NONCANONICAL**
- canonical omission remains unresolved
- publication-blocking
- critic findings do not resolve this

## Frozen linkage hashes

- `work/critics/G4-20260908-001/review_input.jsonl`: `5a07c32c9680032eaa69f268b8160c3460f1b2ebdf7c9a6b547688b81d4f526f`
- `work/critics/G4-20260908-001/critic-a.jsonl`: `e527f6b999d3e06aeaa883de26264a9b29dc3e394c2f9f8d5437797dbba72daf`
- `work/critics/G4-20260908-001/critic-b.jsonl`: `ba0bb2822a4cb711d51388e025deb73ea25980f22a435e81e7bc9864d1ace52e`
- `work/synthesis/G2-20260908-001/candidates.jsonl`: `76462191d3ad2a83c878982a1460443f322437e547b747f6267f4a29d887c619`
- `work/backtranslation/G3-20260908-001/back_translation.jsonl`: `e674a7f0a69ed05c554eaade38e4dbd8025c1f34df0499a8fc4cc9a15c99f00f`
- `work/critics/G4-20260908-001/combined_findings.jsonl`: `29d8ec2a0f8588de7a331088be0181eb169c84337e390d273957f2b86e1e5f19`
- `work/critics/G4-20260908-001/G4_REVIEW_REPORT.md` is this report

## G4 does not adjudicate or revise Finnish wording

This consolidation retains Critic A and Critic B proposed Finnish strings as
review evidence only. It does not apply them. The current G2 Finnish candidate
remains the Finnish wording under review. G5 human disposition is still
required for all 54 translatable units. `requires_G5_human_disposition` marks
items needing particular attention; it is not the complete G5 requirement and
is not a G5 disposition.

This consolidation does not mark the G4 gate as passed.
