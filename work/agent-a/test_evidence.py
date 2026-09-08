import copy
import json

import pytest
from validate_evidence import HERE, validate


def test_current_evidence():
    assert validate()['translated'] == 54


@pytest.mark.parametrize('attack', ['missing', 'extra', 'duplicate', 'hash', 'english', 'blank', 'provenance', 'approval', 'negation', 'agency', 'authority'])
def test_rejects_corrupted_evidence(tmp_path, attack):
    rows = [json.loads(line) for line in (HERE / 'candidates.jsonl').read_text(encoding='utf-8').splitlines()]
    if attack == 'missing':
        rows.pop()
    elif attack == 'extra':
        extra = copy.deepcopy(rows[0])
        extra['unit_id'] = 'S4A-2026-999'
        rows.append(extra)
    elif attack == 'duplicate':
        rows.append(copy.deepcopy(rows[0]))
    elif attack == 'hash':
        rows[0]['source_text_sha256'] = '0' * 64
    elif attack == 'english':
        rows[0]['extensions']['g1_agent_a']['source_text_en'] += ' invented'
    elif attack == 'blank':
        rows[0]['candidate_fi'] = '  '
    elif attack == 'provenance':
        rows[0]['extensions']['g1_agent_a']['source_contract']['source_kind'] = 'official_change_requirement'
    elif attack == 'approval':
        rows[0]['status'] = 'HUMAN_APPROVED'
    elif attack == 'negation':
        rows[-1]['candidate_fi'] = 'Maksansiirto on mahdollinen.'
    elif attack == 'agency':
        rows[9]['candidate_fi'] = rows[9]['candidate_fi'].replace('valitsee', 'määrätään')
    elif attack == 'authority':
        rows[-1]['extensions']['g1_agent_a']['frozen_record']['publication_blocking'] = False
    path = tmp_path / 'corrupt.jsonl'
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    with pytest.raises(Exception):
        validate(path)
