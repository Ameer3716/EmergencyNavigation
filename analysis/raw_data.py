"""Read raw simulation evidence without plotting or statistics dependencies."""
import csv
import xml.etree.ElementTree as ET
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


def incident_observation(path):
    stopped = {f'incidentQueue{i}': [] for i in range(3)}
    planned = {key: [] for key in stopped}
    seen = {key: [] for key in stopped}
    maximum = 0
    for _, step in ET.iterparse(path, events=('end',)):
        if step.tag != 'timestep':
            continue
        time = float(step.get('time'))
        count = 0
        for vehicle in step:
            identity = vehicle.get('id')
            if identity in stopped:
                seen[identity].append(time)
                if vehicle.get('lane') == 'C1C2_0' and float(vehicle.get('speed')) < .1:
                    stopped[identity].append(time)
                    if 90 <= time < 250:
                        planned[identity].append(time)
                        count += 1
        maximum = max(maximum, count)
        step.clear()
    return {key: {'samples': len(times), 'first_s': min(times) if times else None,
                  'last_s': max(times) if times else None,
                  'requested_departure_s': 90 + int(key[-1]),
                  'first_seen_s': min(seen[key]) if seen[key] else None,
                  'incident_samples': len(planned[key]),
                  'incident_first_s': min(planned[key]) if planned[key] else None,
                  'incident_last_s': max(planned[key]) if planned[key] else None}
            for key, times in stopped.items()}, maximum
