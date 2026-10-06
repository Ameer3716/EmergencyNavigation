"""Read raw simulation evidence without plotting or statistics dependencies."""
import csv
from collections import defaultdict
from pathlib import Path


def scalars(path: Path) -> dict[str, list[float]]:
    data = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[0] == "scalar":
            try:
                data[fields[2]].append(float(fields[3]))
            except ValueError:
                pass
    return data


def events(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
