"""Additive G1-A audit sealing. Never rebuild or modify translation evidence."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from verify_g1_a_audit import (
    BLOCKED_PARTS,
    INDEX,
    MANIFEST,
    check_payload,
    digest,
    recorded_relative,
    safe_name,
    verify,
)

ROOT = Path(__file__).resolve().parents[1]
NAME = 'SPICT4ALL-FI-G1-A-forward-translation-audit-20260908.zip'
WP = 'WP-G1-A-AUDIT-PACKAGE-001'


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def run(args, cwd=ROOT):
    env = dict(os.environ, PYTHONPATH=str(cwd / 'src'), PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8')
    value = {'args': args, 'cwd': str(cwd), 'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    print('CHECK', ' '.join(args[:3]), p.returncode, flush=True)
    if p.returncode:
        raise ValueError(json.dumps(value, ensure_ascii=False))
    return value


def git_state():
    chunks = []
    for args in (['rev-parse', 'HEAD'], ['branch', '--show-current'], ['status', '--short', '--untracked-files=all'], ['diff', '--stat'], ['diff', '--cached', '--stat']):
        p = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
        chunks.append('git ' + ' '.join(args) + '\n' + p.stdout)
    return '\n'.join(chunks)


def collect():
    selected = set()
    excluded = []
    def add(name):
        safe_name(name)
        p = ROOT / name
        if p.is_symlink() or p.is_junction() or not p.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError('External path or link rejected: ' + name)
        if not p.is_file():
            raise ValueError('Missing required input: ' + name)
        selected.add(name)
    def tree(name, suffix=None):
        base = ROOT / name
        for current, dirs, files in os.walk(base, followlinks=False):
            keep = []
            for d in dirs:
                p = Path(current) / d
                if d.lower() in BLOCKED_PARTS or d.endswith('.egg-info'):
                    excluded.append({'path': p.relative_to(ROOT).as_posix() + '/', 'reason': 'Excluded cache/temp/runtime directory; not traversed'})
                elif p.is_symlink() or p.is_junction():
                    raise ValueError('Linked directory rejected')
                else:
                    keep.append(d)
            dirs[:] = keep
            for f in files:
                p = Path(current) / f
                if suffix is None or p.suffix == suffix:
                    add(p.relative_to(ROOT).as_posix())
    tree('work/agent-a')
    # T0/T1 evidence closure is required to rerun the original validators offline.
    # It is supplementary verification evidence, not an assertion all was read in G1.
    for folder in ('terminology', 'data/Sanasto', 'config', 'schemas', 'templates'):
        tree(folder)
    for folder in ('src/spict4all', 'tests'):
        tree(folder, '.py')
    metadata = json.loads((ROOT / 'work/agent-a/run_metadata.json').read_text(encoding='utf-8'))
    for r in metadata['inputs']:
        add(recorded_relative(r['path']))
    corrections = json.loads((ROOT / 'terminology/adjudication/enrichment/T1_1_integrity_path_corrections.json').read_text(encoding='utf-8'))['path_corrections']
    for lock in (ROOT / 'terminology/adjudication').rglob('*input_integrity.json'):
        for name in json.loads(lock.read_text(encoding='utf-8'))['protected_files']:
            if name.startswith('work/'):
                # Historical other-role placeholders are referenced, never opened/packaged.
                continue
            add(corrections.get(name, name))
    for name in ('pyproject.toml', 'requirements-dev.lock', 'tools.ps1',
                 'scripts/create_g1_a_audit.py', 'scripts/verify_g1_a_audit.py',
                 'scripts/validate_t1_adjudication.py', 'scripts/validate_t1_1_enrichment.py',
                 'scripts/validate_t1_2_reduction.py', 'scripts/validate_t1_3_closure.py',
                 'scripts/build_terminology_evidence.py'):
        add(name)
    payload = {n: (ROOT / n).read_bytes() for n in sorted(selected)}
    return payload, excluded


def summary():
    return f'''# G1 Forward Translation A audit

Work package: **{WP}**. Original run: WP-G1-A-INDEPENDENT-FORWARD-TRANSLATION-001.
Role: **Forward Translator A**. Actual model: **GPT-6**. Exact backend variant/effort unavailable.

**54 expected / 54 translated: 53 canonical source units + 1 source requirement. All candidates remain DRAFT.**
No human approval is inferred. No clinical validation is claimed. Mechanical validation results are integrity checks, not approval of translation quality.

Agent B was not inspected. No synthesis was performed. No G2 was performed. No sibling worktree was inspected or packaged. No back-translation or critic output based on another candidate was inspected or included. No translation content was regenerated, changed, or synthesized. No commit or push was performed.

S4A-2026-000 authority remains unresolved and publication-blocking; the normalized title remains canonical but non-insertable pending authority disposition. S4A-REQ-2026-001 remains noncanonical, unresolved, publication-blocking, and non-insertable. Its inclusion as translation evidence is not promotion into canonical source. The genuine wording uncertainty remains **frailty / hauraus**. Original source-authority and human-signoff requirements are preserved.

## Included evidence and exclusion boundary

Every existing non-cache/non-temporary file under work/agent-a is preserved byte-for-byte, including its original check logs, source-linked candidates, initial wording, self-edit history, run metadata, report, Git snapshot, hash manifest, and all four Python tools. The explicit no-cache/temp requirement takes precedence over literal inclusion of temporary subdirectories; excluded directories are listed in the audit manifest and were not traversed. No other work directory is opened or included, even for .gitkeep placeholders.

Every recorded G1 run input is included. Relevant frozen official source files, source and governance ledgers, five terminology reference files, glossary, human decisions, and T0/T1 evidence are included. Supplementary T0/T1 files are the dependency closure needed to rerun repository validators, not a claim that Translator A inspected every such file. The glossary still has **0 APPROVED rows**; explicit human ACCEPT wording decisions do not silently promote glossary rows. T1 closure is terminology readiness, not translation approval. Historical pre-G1 reports retain their original state and dates.

Runtime modules, schemas, tests, configurations, and required validator scripts are included for independent checks. Tests and source code may mention other workflow roles or construct artificial test fixtures; these are not Agent B translation artifacts. Native DOCX sources retain their OOXML container format; no nested .zip audit deliverables are included. No .git, venv, retrieval cache, credentials store, or unrelated deliverable is included. Known credential patterns were screened; this is not a universal proof that all conceivable secrets are absent.

## Independent reproduction and hash coverage

Use Python 3.12+ with requirements-dev.lock installed. Extract into a separate directory and run `python scripts/verify_g1_a_audit.py PATH_TO_ZIP`, keeping the .sha256 and .members.sha256 sidecars beside the ZIP. The verifier maps the original run's absolute F: input paths to exact archive-relative names, never to a sibling or external checkout. It checks all frozen input hashes and recomputes source provenance against packaged official DOCX data in a fresh process using packaged runtime code. Existing evidence files, including their original absolute paths, are unchanged.

The original validate_evidence.py has absolute input paths and therefore is not independently relocatable as written. The new archive verifier supplies the portable archive-relative verification without editing that historical script. Original G1-A checks are additionally rerun against the authorized live worktree after sealing, with new logs directed to ignored audit scratch storage. Repository tests and historical T1 validators run in a fixture made only from authorized source/governance/tooling, with empty historical work placeholders reconstructed from the ledger; those placeholders never enter this ZIP. Source, terminology, candidate, coverage, lint, and type validators are rerun after packaging. Exact post-sealing logs and results are in the SHA-bound .verification.json companion. The internal G1_A_AUDIT_VALIDATION_RESULTS.json records pre-sealing checks and points to that later companion; it makes no circular claim about its own final ZIP bytes.

Sorted member names and fixed ZIP timestamps/permissions are used. G1_A_AUDIT_MANIFEST.json lists all members and hashes payload members excluding itself and G1_A_AUDIT_FILE_HASHES.tsv. The TSV additionally hashes the manifest, but excludes itself. The detached .members.sha256 covers every ZIP member, including both index files. The detached .sha256 hashes the final ZIP. This avoids recursive self-hashes. CRC, exact membership, all member hashes, frozen manifests, candidates, provenance, and exclusion rules are rechecked after reopening the archive.

The original G1 report records 311 repository tests plus 12 Agent A tests passed. This package records newly executed outcomes separately, preserving original logs. Hashes prove byte consistency, not all historical model access; historical independence is the translator's recorded attestation plus explicit collection boundaries and inspectable archive membership. No global G1 completion, clinical validity, or release approval is inferred.
'''.encode()


def main():
    destination = ROOT / 'deliverables/audit' / NAME
    sidecars = [Path(str(destination) + suffix) for suffix in ('.sha256', '.members.sha256', '.verification.json')]
    if destination.exists() or any(p.exists() for p in sidecars):
        raise FileExistsError('Existing audit delivery: refusing overwrite')
    # Failure in existing evidence is a hard stop, before any delivery is created.
    existing_check = run(['work/agent-a/validate_evidence.py'])
    payload, excluded = collect()
    initial = {n: digest(b) for n, b in payload.items()}
    pre = check_payload(payload)
    payload['G1_A_AUDIT_SUMMARY.md'] = summary()
    payload['G1_A_GIT_STATE.txt'] = git_state().encode('utf-8')
    payload['G1_A_AUDIT_VALIDATION_RESULTS.json'] = encode({
        'work_package': WP, 'checked_at_utc': datetime.now(UTC).isoformat(),
        'stage': 'BEFORE_SEALING', 'existing_g1_a_validation': existing_check,
        'payload_checks': pre, 'post_sealing_results': NAME + '.verification.json',
    })
    names = sorted(set(payload) | {MANIFEST, INDEX})
    payload[MANIFEST] = encode({
        'work_package': WP, 'original_run': 'WP-G1-A-INDEPENDENT-FORWARD-TRANSLATION-001',
        'members': names, 'payload_sha256': {n: digest(b) for n, b in sorted(payload.items())},
        'original_run_files': sorted(n for n in initial if n.startswith('work/agent-a/')),
        'repository_input_sha256': initial, 'excluded_directories': excluded,
        'collection_root': str(ROOT), 'collection_policy': 'Explicit current-worktree files and authorized roots only; work traversal restricted to agent-a, with temp/cache pruning.',
        'recorded_run_input_mapping': {r['path']: recorded_relative(r['path']) for r in json.loads(payload['work/agent-a/run_metadata.json'])['inputs']},
        'hash_coverage': 'Manifest excludes its own and TSV hashes. TSV covers manifest. Detached .members.sha256 covers every member.',
    })
    payload[INDEX] = ('path\tsha256\tbytes\n' + ''.join(f'{n}\t{digest(b)}\t{len(b)}\n' for n, b in sorted(payload.items()))).encode('utf-8')
    check_payload(payload)
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for n, b in sorted(payload.items()):
            info = zipfile.ZipInfo(n, (2026, 9, 8, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100444 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, b, compresslevel=9)
    zip_sha = digest(destination.read_bytes())
    with sidecars[0].open('x', encoding='utf-8') as f:
        f.write(f'{zip_sha}  {NAME}\n')
    with sidecars[1].open('x', encoding='utf-8') as f:
        f.write(''.join(f'{digest(b)}  {n}\n' for n, b in sorted(payload.items())))
    archive = verify(destination)
    print('SEALED', json.dumps(archive), flush=True)
    # Existing runner is imported, never rebuilt/edited. Only its new-log target changes.
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    scratch = ROOT / 'tmp' / ('g1-a-audit-post-' + stamp)
    scratch.mkdir(parents=True, exist_ok=False)
    wrapper = 'import sys; from pathlib import Path; sys.path.insert(0,str(Path("work/agent-a").resolve())); import run_checks; run_checks.HERE=Path(sys.argv[1]); run_checks.main()'
    post_runner = run(['-c', wrapper, str(scratch)])
    command_file, = list((scratch / 'checks').glob('*/commands.json'))
    post = json.loads(command_file.read_text(encoding='utf-8'))
    for r in post['results']:
        r['output'] = (ROOT / r['log']).read_text(encoding='utf-8')
    fixture = Path(post['results'][0]['cwd'])
    extra = [run(['scripts/' + name], fixture) for name in ('validate_t1_adjudication.py', 'validate_t1_1_enrichment.py', 'validate_t1_2_reduction.py')]
    extra.append(run(['-m', 'ruff', 'check', 'work/agent-a/build_evidence.py', 'work/agent-a/validate_evidence.py', 'work/agent-a/test_evidence.py', 'work/agent-a/run_checks.py']))
    extra.append(run(['work/agent-a/validate_evidence.py']))
    for n, sha in initial.items():
        if digest((ROOT / n).read_bytes()) != sha:
            raise ValueError('Original input changed: ' + n)
    final = verify(destination)
    if final['sha256'] != zip_sha:
        raise ValueError('Sealed ZIP changed')
    with sidecars[2].open('xb') as f:
        f.write(encode({'work_package': WP, 'completed_at_utc': datetime.now(UTC).isoformat(),
                        'archive_verification': final, 'post_packaging_existing_runner': post_runner,
                        'post_packaging_checks': post, 'additional_validators': extra,
                        'all_packaged_repository_bytes_unchanged': True,
                        'original_run_unchanged': True, 'no_translation_changes': True,
                        'no_commit': True, 'no_push': True, 'no_g2': True,
                        'git_state_after_packaging': git_state()}))
    print('COMPLETE', json.dumps(final), flush=True)


if __name__ == '__main__':
    main()
