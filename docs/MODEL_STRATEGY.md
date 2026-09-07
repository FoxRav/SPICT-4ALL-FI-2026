# Model strategy

The goal is **model diversity plus process separation**, not majority voting.

## Primary three-agent setup
- Agent A: GPT-5.6 Sol Medium - independent forward translation.
- Agent B: Claude Fable 5.1 High - independent forward translation.
- Agent C: Claude Opus 5 High - source-grounded synthesis and disagreement accounting.

## Supporting roles
- GPT-5.6 Sol Medium in a fresh isolated session: blind FI->EN back-translation.
- Cursor Grok 4.6 Medium: adversarial critic / dissent detector, not final authority.
- Codex 5.3 Medium: code, schemas, tests, orchestration and report generation.
- Fast/cheap models: mechanical tasks only.

## Why no single model is final authority
Agreement between models can still be correlated error. The final unit-level decision remains human, and real-world testing remains separate.

## Important operational rule
Record the exact model label, effort setting, date, prompt version and input artifact hash for every run. Model names and availability can change over time.
