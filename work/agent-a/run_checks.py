"""Run checks without reading another translation workspace; keep every log."""
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime

from build_evidence import HERE, ROOT, write_new
from validate_evidence import validate


def main():
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    out = HERE / 'checks' / stamp
    out.mkdir(parents=True, exist_ok=False)
    scratch = HERE / 'tmp' / stamp
    scratch.mkdir(parents=True, exist_ok=False)
    # Never copy or traverse work/{agent-b,synthesis,backtranslation,critics,...}.
    for name in ('sources', 'data', 'config', 'terminology', 'docs', 'schemas', 'src', 'tests', 'scripts', 'templates'):
        shutil.copytree(ROOT / name, scratch / name, ignore=shutil.ignore_patterns('__pycache__', '*.egg-info'))
    for name in ('AGENTS.md', 'pyproject.toml', 'README.md'):
        shutil.copyfile(ROOT / name, scratch / name)
    lock = json.loads((ROOT / 'terminology/adjudication/T1_3_input_integrity.json').read_text(encoding='utf-8'))
    for name in lock['work_files']:
        assert name.startswith('work/') and name.endswith('/.gitkeep') and '..' not in name
        placeholder = scratch / name
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        placeholder.touch(exist_ok=False)
    results = []

    def run(label, args, cwd=ROOT):
        env = dict(os.environ, PYTHONPATH=str(cwd / 'src'), PYTHONIOENCODING='utf-8')
        result = subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8')
        log = out / (label + '.txt')
        with log.open('x', encoding='utf-8') as f:
            f.write(result.stdout + result.stderr)
        results.append({'label': label, 'args': args, 'cwd': str(cwd), 'exit_code': result.returncode, 'log': str(log.relative_to(ROOT))})
        print(f'{label}: exit {result.returncode}', flush=True)

    run('repository_tests_in_pre_g1_fixture', ['-m', 'pytest', '-q'], scratch)
    run('t1_closure_in_pre_g1_fixture', ['scripts/validate_t1_3_closure.py'], scratch)
    run('agent_a_tests', ['-m', 'pytest', 'work/agent-a/test_evidence.py', '-q'])
    for command in ('verify-sources', 'validate-terminology', 'validate-canonical', 'validate-requirements', 'validate-governance'):
        run(command, ['-m', 'spict4all.cli', command])
    run('candidate_schema_and_coverage', ['-m', 'spict4all.cli', 'validate-artifact', 'work/agent-a/candidates.jsonl', '--schema', 'schemas/translation_candidate.schema.json', '--require-coverage'])
    run('coverage', ['-m', 'spict4all.cli', 'check-coverage', 'work/agent-a/candidates.jsonl'])
    run('repository_lint', ['-m', 'ruff', 'check', 'src', 'scripts', 'tests'])
    run('repository_types', ['-m', 'mypy', '--strict', 'src/spict4all'])
    write_new(out / 'evidence_validation.json', validate())
    write_new(out / 'commands.json', {'started_at_utc': stamp, 'fixture_scope': 'Authorized source/governance/tooling only. Empty historical work placeholders reconstructed from T1 integrity ledger; no existing work directory copied or traversed.', 'results': results})
    print(out)
    if any(r['exit_code'] for r in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
