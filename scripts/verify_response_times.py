#!/usr/bin/env python3
"""
Verify raw EM generation times, EV arrival times, departure times, and stored response/travel times across all 450 runs.
Exports:
  1. artifacts/response_time_verification.csv
  2. artifacts/event_timeline_verification.csv
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "results/raw"
LOG_DIR = ROOT / "artifacts/logs/batch"
INDIV_CSV = ROOT / "results/processed/individual_runs-batch.csv"
OUT_CSV = ROOT / "artifacts/response_time_verification.csv"
OUT_TIMELINE_CSV = ROOT / "artifacts/event_timeline_verification.csv"


def extract_emergency_log(log_path: Path) -> dict[str, float | None]:
    info = {
        "accident_occurrence": None,
        "accident_detection": None,
        "em_generation": None,
        "ev_receipt": None
    }
    if not log_path.exists():
        return info
    with open(log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            action = r.get("action")
            if action == "accident_occurrence":
                info["accident_occurrence"] = float(r.get("eventTime", 60.0))
            elif action == "accident_detection":
                info["accident_detection"] = float(r.get("eventTime", 0.0))
            elif action == "generated":
                t_gen = r.get("generationTime") or r.get("eventTime")
                if t_gen:
                    info["em_generation"] = float(t_gen)
            elif action == "ev_processed":
                info["ev_receipt"] = float(r.get("eventTime", 0.0))
    return info


def extract_scalars(sca_path: Path) -> dict[str, float]:
    data = {}
    if not sca_path.exists():
        return data
    with open(sca_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 4 and parts[0] == "scalar":
                try:
                    data[parts[2]] = float(parts[3])
                except ValueError:
                    pass
    return data


def main():
    with open(INDIV_CSV, "r", encoding="utf-8") as f:
        indiv_rows = list(csv.DictReader(f))

    print(f"Loaded {len(indiv_rows)} individual runs.")

    resp_records = []
    timeline_records = []

    counts = {
        "PASS": 0,
        "FAIL": 0,
        "NOT_APPLICABLE_NETWORK_PARTITION": 0,
        "MISSING_SOURCE_DATA": 0,
        "UNVERIFIED": 0
    }

    for row in indiv_rows:
        cfg = row["configuration"]
        density = row["density"]
        seed = int(row["seed"])
        stored_resp = float(row["ev_response_s"]) if row["ev_response_s"] else None
        stored_travel = float(row["ev_travel_s"]) if row.get("ev_travel_s") else None

        stem = f"{cfg}-{density}-seed{seed}"
        sca_path = RAW_DIR / f"{stem}.sca"
        em_path = LOG_DIR / f"emergency-{stem}.csv"

        sca_data = extract_scalars(sca_path)
        em_data = extract_emergency_log(em_path)

        # EM generation time: check sca first, then emergency log
        em_gen = sca_data.get("emGenerationTime")
        if em_gen is None:
            em_gen = em_data.get("em_generation")

        ev_arr = sca_data.get("evArrivalTime")
        ev_dep = sca_data.get("evDepartureTime")
        ev_recv = em_data.get("ev_receipt")
        acc_occ = em_data.get("accident_occurrence", 60.0)
        acc_det = em_data.get("accident_detection")
        is_delivered = sca_data.get("accidentArrivalConfirmed", 0) == 1

        if is_delivered:
            if em_gen is not None and ev_arr is not None and stored_resp is not None:
                calc_resp = round(ev_arr - em_gen, 4)
                diff = round(abs(calc_resp - stored_resp), 6)
                if diff < 1e-4:
                    status = "PASS"
                else:
                    status = "FAIL"
            else:
                calc_resp = None
                diff = None
                status = "MISSING_SOURCE_DATA"

            calc_travel = round(ev_arr - ev_dep, 4) if (ev_arr is not None and ev_dep is not None) else None
        else:
            # Network partition run
            status = "NOT_APPLICABLE_NETWORK_PARTITION"
            calc_resp = None
            diff = None
            calc_travel = None

        counts[status] += 1

        # Response verification row (strictly numeric or empty string)
        resp_records.append({
            "density": density,
            "configuration": cfg,
            "seed": seed,
            "raw_em_generation_s": em_gen if em_gen is not None else "",
            "raw_ev_arrival_s": ev_arr if is_delivered and ev_arr is not None else "",
            "calculated_response_s": calc_resp if calc_resp is not None else "",
            "stored_response_s": stored_resp if is_delivered and stored_resp is not None else "",
            "difference_s": diff if diff is not None else "",
            "status": status
        })

        # Event timeline verification row
        timeline_records.append({
            "density": density,
            "configuration": cfg,
            "seed": seed,
            "accident_trigger_s": acc_occ if acc_occ is not None else "",
            "accident_detection_s": acc_det if acc_det is not None else "",
            "em_generation_s": em_gen if em_gen is not None else "",
            "ev_receipt_s": ev_recv if is_delivered and ev_recv is not None else "",
            "ev_departure_s": ev_dep if is_delivered and ev_dep is not None else "",
            "ev_arrival_s": ev_arr if is_delivered and ev_arr is not None else "",
            "stored_travel_time_s": stored_travel if is_delivered and stored_travel is not None else "",
            "stored_response_time_s": stored_resp if is_delivered and stored_resp is not None else "",
            "calculated_travel_time_s": calc_travel if calc_travel is not None else "",
            "calculated_response_time_s": calc_resp if calc_resp is not None else "",
            "status": status
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=resp_records[0].keys())
        writer.writeheader()
        writer.writerows(resp_records)

    with open(OUT_TIMELINE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=timeline_records[0].keys())
        writer.writeheader()
        writer.writerows(timeline_records)

    print(f"Exported {len(resp_records)} response verification records to {OUT_CSV}")
    print(f"Exported {len(timeline_records)} event timeline records to {OUT_TIMELINE_CSV}")
    print("Classification summary:")
    for k, v in counts.items():
        print(f"  {k}: {v}")

    # Strict assertion
    assert counts["PASS"] == 425, f"Expected 425 PASS, got {counts['PASS']}"
    assert counts["NOT_APPLICABLE_NETWORK_PARTITION"] == 25, f"Expected 25 NOT_APPLICABLE_NETWORK_PARTITION, got {counts['NOT_APPLICABLE_NETWORK_PARTITION']}"
    assert counts["FAIL"] == 0, f"Expected 0 FAIL, got {counts['FAIL']}"
    assert counts["MISSING_SOURCE_DATA"] == 0, f"Expected 0 MISSING_SOURCE_DATA, got {counts['MISSING_SOURCE_DATA']}"

    # Verify no row with missing arrival/generation is marked PASS
    for r in resp_records:
        if r["status"] == "PASS":
            assert r["raw_em_generation_s"] != "" and r["raw_ev_arrival_s"] != "", f"PASS row has blank timestamp: {r}"
            assert float(r["difference_s"]) < 1e-4

    print("All response-time verification assertions passed successfully.")


if __name__ == "__main__":
    main()
