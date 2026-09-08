"""Package Agent A wording with verified source evidence; refuse overwrites."""
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from spict4all.cli import _load_canonical_units, _load_requirements
from spict4all.requirements import build_translation_evidence_sources
from spict4all.runs import build_run_metadata
from spict4all.units import load_source_units

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUN_ID = "WP-G1-A-INDEPENDENT-FORWARD-TRANSLATION-001"


def write_new(path, value, jsonl=False):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        if jsonl:
            for row in value:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        else:
            f.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def sources():
    canonical = _load_canonical_units(ROOT, load_source_units(ROOT / "data/source_units.jsonl"))
    requirements = _load_requirements(ROOT, canonical)
    return build_translation_evidence_sources(canonical, requirements.requirements)


def main():
    evidence = sources()
    wording = json.loads((HERE / "translation_input.json").read_text(encoding="utf-8"))
    # Transparent translator self-edit before candidate packaging; original retained.
    revisions = {
        "S4A-2026-015": "Sydämen vajaatoiminta tai sydämen verisuonisairaus. Hengenahdistusta tai rintakipua levätessä, liikkuessa tai kävellessä muutaman askeleen.",
        "S4A-2026-025": "Vointi on huonontunut pitkäaikaisten keuhko-ongelmien yhteydessä. Hengenahdistusta levätessä, liikkuessa tai kävellessä muutaman askeleen silloinkin, kun keuhkojen tilanne on parhaimmillaan.",
        "S4A-2026-026": "Viimeksi kuluneen vuoden aikana pahentuneita maksaongelmia, joihin liittyy esimerkiksi seuraavia lisäongelmia:",
    }
    wording.update(revisions)
    assert set(wording) == {s.evidence_id for s in evidence}
    assert len(evidence) == 54
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    notes = {
        "S4A-2026-000": "Title placeholder retained. Canonical normalization does not resolve publication authority.",
        "S4A-2026-004": "Recorded human wording retained with the source's usual-activities scope.",
        "S4A-2026-006": "Carer expressed as a person providing care, without adding formal caregiver status.",
        "S4A-2026-014": "Recorded human wording retained with the source's usual-activities scope.",
        "S4A-2026-020": "Separate canonical dialysis wording retained despite overlap with unit 019.",
        "S4A-2026-021": "Hauraus is an independent plain-language candidate, not an approved term; no age restriction added.",
        "S4A-2026-025": "Chest rendered contextually as the condition of the lungs; best-state qualifier retained.",
        "S4A-2026-045": "Chest infections rendered as lower respiratory tract infections; pneumonia alternative retained.",
        "S4A-2026-049": "All seven domains retained; spiritual rendered broadly as henkisiin ja hengellisiin kysymyksiin. No religious restriction added.",
        "S4A-REQ-2026-001": "Translation evidence only. Noncanonical omission remains unresolved and publication-blocking.",
    }
    frozen = {u['unit_id']: u for u in load_source_units(ROOT / 'data/source_units.jsonl')}
    requirement = json.loads((ROOT / 'data/source_requirements.jsonl').read_text(encoding='utf-8'))
    exception = json.loads((ROOT / 'data/canonical_unit_exceptions.jsonl').read_text(encoding='utf-8'))
    records = []
    for source in evidence:
        uid = source.evidence_id
        audit = {
            "source_text_en": source.exact_source_text_en,
            "source_contract": asdict(source),
            "frozen_record": frozen.get(uid, requirement),
            "translator_identity": "Forward Translator A",
            "run_id": RUN_ID,
            "run_timestamp_utc": timestamp,
            "model_identity_basis": "Session instructions identify GPT-6; exact backend variant and effort are not exposed. Repository planned GPT-5.6 Sol Medium was not used.",
            "effort_setting": "NOT_EXPOSED",
            "uncertainty": "Does plain-language hauraus convey the full frailty concept adequately to the target reader? This is a wording uncertainty, not a reopened pre-G1 blocker." if uid == "S4A-2026-021" else "",
        }
        if uid == "S4A-2026-000":
            audit['canonical_exception'] = exception
        records.append({
            "unit_id": uid, "source_text_sha256": source.source_text_sha256,
            "model": "GPT-6", "session_id": RUN_ID,
            "prompt_version": RUN_ID, "candidate_fi": wording[uid],
            "decision_note": notes.get(uid, ""), "issues": [], "status": "DRAFT",
            "extensions": {"g1_agent_a": audit},
        })
    inputs = [
        'AGENTS.md', 'README.md', 'pyproject.toml', 'requirements-dev.lock',
        'docs/METHODOLOGY.md', 'docs/WORKFLOW.md', 'docs/MODEL_STRATEGY.md',
        'docs/OFFICIAL_TRANSLATION_GUIDANCE.md', 'prompts/01-agent-a-forward.md',
        'data/source_units.jsonl', 'data/source_requirements.jsonl',
        'data/canonical_unit_exceptions.jsonl', 'data/canonical_unit_manifest.json',
        'data/governance_integrity_manifest.json', 'sources/manifests/source_manifest.json',
        'schemas/translation_candidate.schema.json', 'schemas/run_metadata.schema.json',
        'terminology/terms.csv', 'terminology/README.md',
        'terminology/adjudication/human_terminology_decisions.tsv',
        'terminology/adjudication/T1_2_reclassification.json',
        'terminology/adjudication/T1_TERMINOLOGY_CLOSURE_REPORT.md',
        'terminology/adjudication/T1_3_project_owner_disposition.json',
        'terminology/extracted/terminology_evidence.jsonl',
        'terminology/adjudication/enrichment/TERM-SRC-006-terveyskirjasto-evidence.jsonl',
        'work/agent-a/translation_input.json', 'work/agent-a/build_evidence.py',
    ]
    inputs.extend(str(p.relative_to(ROOT)) for p in (ROOT / 'sources/official').iterdir() if p.is_file())
    metadata = build_run_metadata(RUN_ID, 'Forward Translator A', [ROOT / p for p in inputs], created_at_utc=timestamp)
    write_new(HERE / 'run_metadata.json', metadata)
    write_new(HERE / 'self_edit_log.json', {
        'kind': 'TRANSLATOR_A_SELF_EDIT_BEFORE_PACKAGING', 'timestamp_utc': timestamp,
        'initial_wording': 'translation_input.json', 'replacements': revisions,
        'reasons': {'015_and_025': 'Explicit breathlessness also at rest.', '026': 'Rolling past year, avoiding a previous-calendar-year reading.'},
    })
    write_new(HERE / 'candidates.jsonl', records, jsonl=True)
    print(f'Packaged {len(records)} DRAFT candidates at {timestamp}')


if __name__ == '__main__':
    main()
