import json
from pathlib import Path

from spict4all.terminology_closure import validate_closure

if __name__ == "__main__":
    print(json.dumps(validate_closure(Path(__file__).resolve().parents[1]), indent=2))
