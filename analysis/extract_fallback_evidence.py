#!/usr/bin/env python3
"""Extract fallback evidence from current unmodified batch files."""
from pathlib import Path
from process_results import events, scalars, write_csv

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    records = []
    for density in ("low", "medium", "high"):
        for seed in range(1, 31):
            stem = f"MistDynamicFogFallback-{density}-seed{seed}"
            scalar = ROOT / "results/raw" / f"{stem}.sca"
            if not scalar.exists():
                raise SystemExit(f"Missing current run: {scalar}")
            value = scalars(scalar)
            def first(key):
                return value[key][0] if value.get(key) else ""
            logs = ROOT / "artifacts/logs/batch"
            route = events(logs / f"routing-{stem}.csv")
            fallback = events(logs / f"fallback-{stem}.csv")
            em = events(logs / f"emergency-{stem}.csv")
            computed = next((r for r in route if r["action"] == "computed"), {})
            applied = next((r for r in route if r["action"] == "applied"), {})
            generated = next((r for r in em if r["action"] == "generated"), {})
            fb = fallback[0] if fallback else {}
            start = float(computed["decisionStart"]) if computed else ""
            final = float(applied["time"]) if applied else ""
            latency = first("routeDecisionLatency")
            threshold = float(fb["watchdogThreshold"]) if fb else 0.5
            controlled = "config *.node[*].appl.controlledMistStallDelay 900ms" in scalar.read_text(encoding="utf-8")
            records.append({
                "scenario": f"{density} seed {seed}",
                "configuration": "MistDynamicFogFallback", "density": density, "seed": seed,
                "scenario_condition": "controlled_stall" if controlled else "normal",
                "em_generation_time_s": float(generated["generationTime"]) if generated else "",
                "mist_start_s": start,
                "mist_completion_s": final if applied.get("location") == "mist" else "",
                "scheduled_mist_duration_s": float(computed["computationDelay"]) if computed else "",
                "observed_mist_duration_s": float(fb["time"]) - start if fb and start != "" else latency,
                "watchdog_threshold_s": threshold,
                "watchdog_expiry_s": start + threshold if start != "" else "",
                "mist_status": "CONTROLLED_STALL_TIMEOUT" if fb and controlled else ("WATCHDOG_TIMEOUT" if fb else ("COMPLETED" if applied else "NO_EM_DELIVERY")),
                "failure_reason": fb.get("fallbackReason", "none"),
                "fallback_triggered": int(bool(fb)),
                "fallback_trigger_type": "controlled_stall_timeout" if fb and controlled else ("timeout" if fb else "none"),
                "fallback_trigger_time_s": float(fb["time"]) if fb else "",
                "fog_request_time_s": float(fb["fogRequestTime"]) if fb else "",
                "fog_computation_s": first("fogProcessingDelay"),
                "communication_delay_s": first("routeCommunicationDelay"),
                "wait_before_fog_s": first("routeWaitBeforeFog"),
                "final_decision_time_s": final,
                "final_decision_latency_s": latency,
                "final_decision_latency_ms": latency * 1000 if latency != "" else "",
                "applied_route": applied.get("selectedEdges", ""),
                "supplying_tier": applied.get("location", "none"),
            })
    write_csv(ROOT / "results/processed/fallback_validation.csv", records)
    print(f"Extracted {len(records)} runs; {sum(r['fallback_triggered'] for r in records)} controlled/normal fallback activations")


if __name__ == "__main__":
    main()
