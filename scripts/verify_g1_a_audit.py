"""Verify G1-A archive hashes and source-linked evidence without another worktree."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import asdict
from pathlib import Path, PurePosixPath, PureWindowsPath

PREFIX = "G1_A_"
MANIFEST = PREFIX + "AUDIT_MANIFEST.json"
INDEX = PREFIX + "AUDIT_FILE_HASHES.tsv"
ORIGINAL_ROOT = PureWindowsPath("F:/-DEV-/120.SPICT-G1-A")
BLOCKED_PARTS = {".git", ".venv", "venv", ".firecrawl", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", "tmp", "temp", "cache"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name
            or any(x.lower() in BLOCKED_PARTS for x in p.parts)
            or p.suffix.lower() in {".zip", ".7z", ".rar", ".tar", ".gz", ".pyc", ".tmp"}
            or p.name.lower().startswith('.env')):
        raise ValueError(f"Forbidden archive path: {name}")
    if name.startswith("work/") and not name.startswith("work/agent-a/"):
        raise ValueError(f"Non-Agent-A workspace: {name}")
    if any(x.lower() in {"agent-b", "g1-forward-b", "synthesis", "backtranslation", "back-translation", "critics"} for x in p.parts):
        raise ValueError(f"Independence contamination: {name}")
    return name


def recorded_relative(name):
    # Exact recorded worktree prefix; never infer or search sibling paths.
    return safe_name(PureWindowsPath(name).relative_to(ORIGINAL_ROOT).as_posix())


def check_payload(payload):
    for name, data in payload.items():
        safe_name(name)
        if Path(name).suffix.lower() in {'.py', '.json', '.jsonl', '.md', '.txt', '.yaml', '.tsv', '.mjs', '.csv', '.toml', '.lock', '.ps1'}:
            for pattern in (rb'sk-[A-Za-z0-9_-]{24,}', rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'):
                if re.search(pattern, data):
                    raise ValueError(f'Potential credential in {name}')
    def read(name):
        return json.loads(payload[name])
    def check(name, sha, size=None):
        if digest(payload[name]) != sha or (size is not None and len(payload[name]) != size):
            raise ValueError(f'Frozen hash/size mismatch: {name}')
    official = read('sources/manifests/source_manifest.json')
    for r in official:
        check('sources/official/' + r['filename'], r['sha256'], r['bytes'])
    for r in read('data/governance_integrity_manifest.json')['files']:
        check(r['relative_path'], r['sha256'], r['byte_count'])
    terminology = read('terminology/sources/terminology_source_manifest.json')['sources']
    for r in terminology:
        f = r['file_facts']
        check('data/Sanasto/' + f['filename'], f['sha256'], f['byte_count'])
    metadata = read('work/agent-a/run_metadata.json')
    for r in metadata['inputs']:
        check(recorded_relative(r['path']), r['sha256'], r['bytes'])
    artifact = read('work/agent-a/artifact_manifest.json')
    for r in artifact['files']:
        check(safe_name(r['path']), r['sha256'], r['bytes'])
    glossary = list(csv.DictReader(io.StringIO(payload['terminology/terms.csv'].decode('utf-8'))))
    approved = sum(r['status'] == 'APPROVED' for r in glossary)
    if approved != 0:
        raise ValueError('Unexpected APPROVED glossary state')
    def rows(name):
        return [json.loads(line) for line in payload[name].decode('utf-8').splitlines() if line.strip()]
    units = rows('data/source_units.jsonl')
    reqs = rows('data/source_requirements.jsonl')
    candidates = rows('work/agent-a/candidates.jsonl')
    expected = {r['unit_id']: (r['source_text_en'], r['source_text_sha256'], r) for r in units}
    for r in reqs:
        if r['translation_evidence_required']:
            if r['requirement_id'] in expected:
                raise ValueError('Duplicate source identifier')
            expected[r['requirement_id']] = (r['exact_source_text_en'], r['exact_text_sha256'], r)
    ids = [r['unit_id'] for r in candidates]
    if (len(units) != 53 or len({r['unit_id'] for r in units}) != 53
            or len(reqs) != 1 or reqs[0]['requirement_id'] != 'S4A-REQ-2026-001'
            or len(ids) != 54 or len(set(ids)) != 54 or set(ids) != set(expected)):
        raise ValueError('Candidate/source membership mismatch')
    for c in candidates:
        en, sha, frozen = expected[c['unit_id']]
        a = c['extensions']['g1_agent_a']
        if (digest(en.encode()) != sha or c['source_text_sha256'] != sha
                or a['source_text_en'] != en or a['frozen_record'] != frozen
                or not c['candidate_fi'].strip() or c['status'] != 'DRAFT'
                or c['model'] != 'GPT-6' or a['effort_setting'] != 'NOT_EXPOSED'
                or a['translator_identity'] != 'Forward Translator A'
                or a['run_id'] != metadata['run_id'] or c['session_id'] != metadata['run_id']
                or a['run_timestamp_utc'] != metadata['created_at_utc']):
            raise ValueError('Candidate source/status/identity mismatch: ' + c['unit_id'])
        if c['unit_id'] in ('S4A-2026-000', 'S4A-REQ-2026-001'):
            contract = a['source_contract']
            if contract['final_inclusion_status'] != 'UNRESOLVED' or contract['eligible_for_document_insertion']:
                raise ValueError('Unresolved authority altered')
    req = reqs[0]
    if (req['canonical_source_presence'] or not req['publication_blocking']
            or req['final_inclusion_status'] != 'UNRESOLVED'
            or req['conflict_status'] != 'UNRESOLVED_CANONICAL_OMISSION'):
        raise ValueError('Requirement authority changed')
    exception = rows('data/canonical_unit_exceptions.jsonl')[0]
    title = next(c for c in candidates if c['unit_id'] == 'S4A-2026-000')
    if (title['extensions']['g1_agent_a']['canonical_exception'] != exception
            or not exception['publication_blocking'] or exception['authority_status'] != 'AUTHORITY_DECISION_REQUIRED'):
        raise ValueError('Title authority changed')
    return {'candidate_coverage': 'PASS: exactly 54, 53 canonical + 1 requirement; no duplicates/missing/extra',
            'source_hashes_exact_english_frozen_records': 'PASS', 'all_candidates_draft_nonblank': True,
            'approved_glossary_rows': approved, 'official_sources': len(official),
            'terminology_sources': len(terminology), 'run_input_hashes': 'PASS: archive-relative resolution',
            'original_artifact_manifest': 'PASS', 'authority_states_preserved': True,
            'independence_contamination': 'PASS: no prohibited member paths; explicit current-worktree allowlist',
            'secret_screening': 'PASS: known credential patterns; no credential stores selected'}


def verify_tree(root):
    # Called in a fresh subprocess whose PYTHONPATH is the extracted archive only.
    from spict4all.artifacts import validate_jsonl_artifact
    from spict4all.cli import _load_canonical_units, _load_requirements
    from spict4all.coverage import require_complete_coverage
    from spict4all.requirements import build_translation_evidence_sources
    from spict4all.units import load_source_units

    canonical = _load_canonical_units(root, load_source_units(root / 'data/source_units.jsonl'))
    reqs = _load_requirements(root, canonical)
    sources = build_translation_evidence_sources(canonical, reqs.requirements)
    rows = validate_jsonl_artifact(root / 'work/agent-a/candidates.jsonl', root / 'schemas/translation_candidate.schema.json', source_records=sources)
    require_complete_coverage(sources, rows)
    contracts = {s.evidence_id: json.loads(json.dumps(asdict(s))) for s in sources}
    for row in rows:
        if row['extensions']['g1_agent_a']['source_contract'] != contracts[row['unit_id']]:
            raise ValueError('Source provenance/contract mismatch')
    return {'schema': 'PASS', 'coverage': len(rows), 'source_provenance': 'PASS: recomputed from frozen DOCX and governance', 'checkout_independent': True}


def verify(path):
    import os

    sha = digest(path.read_bytes())
    if sha != Path(str(path) + '.sha256').read_text().split()[0]:
        raise ValueError('ZIP SHA mismatch')
    hashes = {}
    for line in Path(str(path) + '.members.sha256').read_text(encoding='utf-8').splitlines():
        value, name = line.split('  ', 1)
        if name in hashes:
            raise ValueError('Duplicate hash entry')
        hashes[name] = value
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if names != sorted(names) or len(names) != len(set(names)) or set(names) != set(hashes):
            raise ValueError('Archive membership mismatch')
        payload = {safe_name(n): z.read(n) for n in names}
        for n, data in payload.items():
            if digest(data) != hashes[n]:
                raise ValueError('Member hash mismatch: ' + n)
        if z.testzip() is not None:
            raise ValueError('CRC failure')
    manifest = json.loads(payload[MANIFEST])
    if manifest['members'] != names or set(manifest['payload_sha256']) != set(names) - {MANIFEST, INDEX}:
        raise ValueError('Internal manifest scope mismatch')
    for n, sha256 in manifest['payload_sha256'].items():
        if hashes[n] != sha256:
            raise ValueError('Manifest payload mismatch')
    for n, sha256 in manifest['repository_input_sha256'].items():
        if hashes.get(n) != sha256:
            raise ValueError('Original repository input mismatch')
    if manifest['original_run_files'] != sorted(n for n in names if n.startswith('work/agent-a/')):
        raise ValueError('Original run inventory mismatch')
    index = list(csv.DictReader(io.StringIO(payload[INDEX].decode()), delimiter='\t'))
    if len(index) != len(names) - 1 or {r['path'] for r in index} != set(names) - {INDEX}:
        raise ValueError('Internal TSV membership mismatch')
    for r in index:
        if hashes[r['path']] != r['sha256'] or len(payload[r['path']]) != int(r['bytes']):
            raise ValueError('Internal TSV hash/size mismatch')
    results = check_payload(payload)
    with tempfile.TemporaryDirectory(prefix='.g1-a-verify-', dir=path.parent) as temp:
        tree = Path(temp)
        for n, data in payload.items():
            target = tree / n
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        env = dict(os.environ, PYTHONPATH=str(tree / 'src'), PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([sys.executable, 'scripts/verify_g1_a_audit.py', '--tree', str(tree)], cwd=tree, env=env, capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            raise ValueError('Extracted source/provenance validation failed: ' + result.stderr)
        results['independent_source_provenance'] = json.loads(result.stdout)
    return {'zip': path.name, 'bytes': path.stat().st_size, 'sha256': sha, 'member_count': len(names),
            'member_hashes': 'PASS: every member', 'crc': 'PASS', 'manifest_membership': 'PASS', **results}


if __name__ == '__main__':
    value = verify_tree(Path(sys.argv[2])) if sys.argv[1] == '--tree' else verify(Path(sys.argv[1]).resolve())
    print(json.dumps(value, ensure_ascii=False, indent=2))
