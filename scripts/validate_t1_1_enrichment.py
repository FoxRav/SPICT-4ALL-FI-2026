"""Validate additive terminology evidence without changing any source authority."""
import json
from pathlib import Path

from spict4all.terminology_enrichment import validate_enrichment

if __name__ == "__main__":
    print(json.dumps(validate_enrichment(Path(__file__).resolve().parents[1]),
                     ensure_ascii=False, indent=2))
