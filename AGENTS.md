# Agent instructions - SPICT-4ALL FI

## Mission
Build and operate a rigorous, reproducible AI-assisted Finnish translation workflow for the official SPICT-4ALL 2026 source material.

## Non-negotiable rules
1. `sources/official/**` is immutable. Never edit, overwrite, rename or regenerate official source files.
2. Never invent source text, clinical meaning, terminology, citations, approvals or validation results.
3. Do not call AI review "clinical validation". Clinical/methodological validation is a human/evidence activity.
4. Every translation unit must retain its `unit_id` and source SHA-256.
5. Independent forward translations must be genuinely independent: Agent B must not see Agent A's candidate.
6. Back-translation must be blind: the back-translator receives the Finnish candidate, not the original English source.
7. Critics report issues; they must not silently rewrite accepted text.
8. Final approval requires explicit human sign-off for every unit.
9. Preserve plain-language intent. Do not make the wording more technical merely because the topic is medical.
10. Preserve meaning precisely: negation, modality, agency, time, severity, alternatives, patient/family choices, and causal relationships.
11. Keep a complete audit trail. No destructive overwrite of prior candidate or review artifacts.
12. Do not claim "zero error" or "validated" unless the required evidence and human approval exist. Use "zero known errors" only after all gates pass.

## Engineering
- Prefer Python 3.12+ for workflow tooling.
- Use deterministic file formats (JSONL/TSV/CSV) for translation evidence.
- Add tests for source integrity, schema validity, missing units, duplicate IDs and hash mismatches.
- No API keys or personal data in Git.
- User performs Git push manually.
