import json
from pathlib import Path

from spict4all.review_reduction import validate_reduction

if __name__ == "__main__":
    print(json.dumps(validate_reduction(Path(__file__).resolve().parents[1]), ensure_ascii=False, indent=2))
