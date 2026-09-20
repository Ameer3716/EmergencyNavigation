#!/usr/bin/env python3
"""Validate the four genuine EM dissemination test runs from their CSV logs."""

import csv
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
logs = root / "artifacts/logs"


def read_run(name: str) -> list[dict[str, str]]:
    with (logs / f"emergency-{name}.csv").open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    assert rows, f"empty {name} log"
    assert all(None not in row for row in rows), f"malformed CSV in {name}"
    actions = [row["action"] for row in rows]
    for action in ("accident_occurrence", "accident_detection", "generated"):
        assert actions.count(action) == 1, f"expected one {action} in {name}"
    occurrence = next(row for row in rows if row["action"] == "accident_occurrence")
    detection = next(row for row in rows if row["action"] == "accident_detection")
    generated = next(row for row in rows if row["action"] == "generated")
    assert float(occurrence["eventTime"]) == 60
    assert float(detection["eventTime"]) - float(occurrence["eventTime"]) >= 3
    assert generated["eventTime"] == detection["eventTime"]
    assert int(generated["remainingHops"]) == (1 if name == "TtlOne" else 10)
    assert int(generated["hopCount"]) == 0
    return rows


direct = read_run("DirectDelivery")
vehicle = read_run("VehicleRelay")
rsu = read_run("RsuRelay")
ttl = read_run("TtlOne")

def processed(rows: list[dict[str, str]]) -> dict[str, str]:
    found = [row for row in rows if row["action"] == "ev_processed"]
    assert len(found) == 1, f"expected one EV delivery, got {len(found)}"
    return found[0]


direct_ev = processed(direct)
assert int(direct_ev["hopCount"]) == 0
assert direct_ev["senderId"].endswith("rsu[2]")

vehicle_ev = processed(vehicle)
assert int(vehicle_ev["hopCount"]) >= 1
assert vehicle_ev["senderId"].startswith("normal")
assert any(row["action"] == "transmit" and row["nodeRole"] == "normal" for row in vehicle)
assert any(row["action"] == "duplicate_discard" and row["duplicateDiscarded"] == "1" for row in vehicle)

rsu_ev = processed(rsu)
assert int(rsu_ev["hopCount"]) >= 1
assert rsu_ev["senderId"].endswith("rsu[1]") or rsu_ev["senderId"].endswith("rsu[0]")
assert sum(row["action"] == "transmit" and row["nodeRole"] == "rsu" for row in rsu) >= 2
assert not any(row["action"] == "transmit" and row["nodeRole"] == "normal" for row in rsu)

assert not any(row["action"] == "ev_processed" for row in ttl)
assert sum(row["action"] == "transmit" for row in ttl) == 1
assert any(row["action"] == "ttl_expired" and row["ttlExpired"] == "1" for row in ttl)

result = {
    "direct_hops": int(direct_ev["hopCount"]),
    "vehicle_relay_hops": int(vehicle_ev["hopCount"]),
    "rsu_relay_hops": int(rsu_ev["hopCount"]),
    "vehicle_duplicate_discards": sum(row["action"] == "duplicate_discard" for row in vehicle),
    "ttl_one_transmissions": sum(row["action"] == "transmit" for row in ttl),
    "ttl_one_expirations": sum(row["action"] == "ttl_expired" for row in ttl),
    "status": "passed",
}
print(json.dumps(result, indent=2))
