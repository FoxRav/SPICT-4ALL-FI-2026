"""Generate only portal data from the explicitly frozen Git evidence."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "6a1a270a9d41953000b401256af0d58f7a3c0576"
RUN = "G5-20260908-001"
IDS = tuple(f"S4A-2026-{n}" for n in ("017", "021", "025", "026", "045", "049"))
QUESTIONS = (
    "Säilyttääkö hyväkuntoinen merkityksen, että henkilö on riittävän hyvässä kunnossa syöpähoitoon, vai voiko se viitata fyysiseen kuntoon?",
    "Mikä ymmärrettävä suomenkielinen ilmaus säilyttää frailty-terveyskäsitteen merkityksen?",
    "Mitä 'when the chest is at its best' tarkoittaa tässä kliinisessä ja yleiskielisessä yhteydessä, ja ilmaiseeko nykyinen suomennos sen oikein?",
    "Säilyttääkö lisäongelmia sanan 'complications' merkityksen riittävästi, vai tarvitaanko täsmällisempi yleiskielinen termi?",
    "Säilyttääkö rintakehän infektioita ilmauksen 'chest infections' tarkoitetun merkityksen?",
    "Säilyttääkö henkisiin ja hengellisiin englannin yhden 'spiritual'-osa-alueen, vai lisääkö se merkitystä?",
)
DATA_PATH = "review-portal/site/review/sami/review-data.json"
CONFIG_PATH = "review-portal/worker/src/review-config.generated.js"


def frozen(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{COMMIT}:{path}"], cwd=ROOT).decode("utf-8")


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def artifacts() -> dict[str, bytes]:
    source_path = "data/source_units.jsonl"
    g5_path = f"work/human-review/{RUN}/human_dispositions.tsv"
    packet_path = f"work/human-review/{RUN}/G5_SAMI_DOMAIN_REVIEW.md"
    g2_path = "work/synthesis/G2-20260908-001/candidates.jsonl"
    # Fail closed if live evidence has drifted from the frozen candidate.
    for path in (source_path, g5_path, packet_path, g2_path):
        if (ROOT / path).read_text(encoding="utf-8") != frozen(path):
            raise ValueError(f"Evidence differs from frozen candidate: {path}")
    sources = {r["unit_id"]: r for r in map(json.loads, frozen(source_path).splitlines())}
    g2 = {r["unit_id"]: r for r in map(json.loads, frozen(g2_path).splitlines())}
    g5 = {r["unit_id"]: r for r in csv.DictReader(io.StringIO(frozen(g5_path)), delimiter="\t")}
    packet = frozen(packet_path)
    units = []
    hashes = {}
    for uid, question in zip(IDS, QUESTIONS, strict=True):
        row, source = g5[uid], sources[uid]
        assert row["source_text_en"] == source["source_text_en"]
        assert row["current_candidate_fi"] == g2[uid]["candidate_fi"]
        assert hashlib.sha256(source["source_text_en"].encode()).hexdigest() == source["source_text_sha256"]
        section = packet.split(f"## {uid}\n", 1)[1].split("\n## ", 1)[0]
        blocks = re.findall(r"```\n(.*?)\n```", section, re.S)
        assert blocks[:2] == [row["source_text_en"], row["current_candidate_fi"]]
        hashes[uid] = source["source_text_sha256"]
        units.append(dict(unit_id=uid, source_text_en=row["source_text_en"],
                          current_candidate_fi=row["current_candidate_fi"],
                          neutral_review_question=question,
                          review_priority=row["combined_review_priority"],
                          existing_human_decision_note={
                              IDS[0]: "Aiempi Project Owner -sanamuoto on uudelleen arvioitavana.",
                              IDS[1]: "Lopullista ihmisen päättämää termiä ei ole kirjattu.",
                              IDS[5]: "Aiempi päätös koski vain holistic care -termiä, ei spiritual-käsitettä.",
                          }.get(uid, "")))
    data = encoded(units)
    config = dict(schema_version="1.0", review_run_id=RUN, review_candidate_commit=COMMIT,
                  review_data_sha256=hashlib.sha256(data).hexdigest(), units=units,
                  source_sha256_by_unit=hashes)
    return {DATA_PATH: data, CONFIG_PATH: b"// Generated; do not edit.\nexport const config = " + encoded(config).rstrip() + b";\n",
            "review-portal/site/review/sami/review-meta.json": encoded({k: v for k, v in config.items() if k not in ("units", "source_sha256_by_unit")})}


def main() -> None:
    for relative, content in artifacts().items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    print("Generated frozen Sami portal data: " + COMMIT)


if __name__ == "__main__":
    main()
