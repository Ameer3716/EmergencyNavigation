#!/usr/bin/env python3
"""Build the delivery from 360 primary runs and 90 waiting-time controls."""
from __future__ import annotations

import csv
import hashlib
import argparse
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "EmergencyNavigation_Reviewed_400m_Submission"
ZIP = ROOT.parent / "EmergencyNavigation_Reviewed_400m_Submission.zip"
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback", "NoPreemptionBaseline")
DENSITIES = ("low", "medium", "high")
EXTENSIONS = ("sca", "vec", "vci")


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Update the existing reviewed package")
    args = parser.parse_args()
    if not (ROOT / "artifacts/audit_report.json").exists():
        raise SystemExit("Run scripts/audit_batch.py first")
    import json
    audit = json.loads((ROOT / "artifacts/audit_report.json").read_text(encoding="utf-8"))
    if not audit.get("passed"):
        raise SystemExit("Batch audit did not pass")
    if not args.refresh and (ZIP.exists() or (OUT.exists() and any(path.name != "Emergency_Vehicle_Navigation_Final_Submission.docx" for path in OUT.iterdir()))):
        raise SystemExit(f"Destination already contains a package: {OUT} or {ZIP}")
    OUT.mkdir(exist_ok=True)
    if not (OUT / "Emergency_Vehicle_Navigation_Final_Submission.docx").exists():
        raise SystemExit("Generate the reviewed Word document before packaging")

    for name in ("README.md", "PROJECT_SPEC.md", "AGENTS.md"):
        copy(ROOT / name, OUT / name)
    for name in ("METHODOLOGY.md", "VERIFICATION.md", "PROGRESS.md", "EXPERIMENTS.md", "INSTALLATION.md", "PROCESS_AND_GRAPHS.md"):
        copy(ROOT / "docs" / name, OUT / "docs" / name)
    for name in ("summary-batch.csv", "individual_runs-batch.csv", "paired_comparisons.csv",
                 "fallback_validation.csv", "graph_plot_data.csv", "before_after_headline.csv", "summary-cohorts.csv"):
        copy(ROOT / "results/processed" / name, OUT / "results/processed" / name)
    copy(ROOT / "artifacts/audit_report.json", OUT / "artifacts/audit_report.json")
    copy(ROOT / "artifacts/sample_validation.json",
         OUT / "artifacts/sample_validation.json")
    for path in (ROOT / "results/graphs").glob("*.png"):
        copy(path, OUT / "results/graphs" / path.name)
    for path in (ROOT / "analysis").glob("*.py"):
        copy(path, OUT / "analysis" / path.name)
    for name in ("build.sh", "run_batch_env.sh", "run_batch.py", "generate_demand.py",
                 "audit_batch.py", "verify_response_times.py", "generate_final_graph.py",
                 "write_final_reports.py", "generate_reviewed_submission.py",
                 "generate_final_docx.py", "package_reviewed_submission.py", "validate_review_sample.py"):
        copy(ROOT / "scripts" / name, OUT / "scripts" / name)
    for path in (ROOT / "src").rglob("*"):
        if path.is_file() and (path.suffix in (".cc", ".h", ".ned", ".msg") or path.name == "Makefile"):
            copy(path, OUT / "src" / path.relative_to(ROOT / "src"))
    for path in (ROOT / "simulations/grid").iterdir():
        if path.is_file():
            copy(path, OUT / "simulations/grid" / path.name)
    for density in DENSITIES:
        for seed in range(1, 31):
            folder = ROOT / "simulations/batch" / f"{density}-seed{seed}"
            for suffix in ("trips.xml", "rou.xml"):
                name = f"normal-{density}-seed{seed}.{suffix}"
                copy(folder / name, OUT / "simulations/batch" / folder.name / name)
    for config in CONFIGS:
        for density in DENSITIES:
            for seed in range(1, 31):
                stem = f"{config}-{density}-seed{seed}"
                for path in (ROOT / "artifacts/logs/batch").glob(f"*-{stem}.csv"):
                    copy(path, OUT / "artifacts/logs/batch" / path.name)
                stdout = ROOT / "artifacts/logs/batch" / f"{stem}-stdout.txt"
                copy(stdout, OUT / "artifacts/logs/batch" / stdout.name)
                manifest_file = ROOT / "artifacts/logs/batch" / f"manifest-{stem}.json"
                copy(manifest_file, OUT / "artifacts/logs/batch" / manifest_file.name)
                sumo_summary = ROOT / "artifacts/logs/batch" / f"sumo-summary-{stem}.xml"
                copy(sumo_summary, OUT / "artifacts/logs/batch" / sumo_summary.name)

    raw = ROOT / "results/raw"
    manifest = []
    for config in CONFIGS:
        for density in DENSITIES:
            for seed in range(1, 31):
                stem = f"{config}-{density}-seed{seed}"
                for extension in EXTENSIONS:
                    path = raw / f"{stem}.{extension}"
                    digest = hashlib.sha256()
                    with path.open("rb") as handle:
                        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                            digest.update(block)
                    manifest.append({"configuration": config, "density": density, "seed": seed,
                                     "raw_file": path.name, "size_bytes": path.stat().st_size,
                                     "sha256": digest.hexdigest()})
    manifest_path = OUT / "results/raw_evidence_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=manifest[0].keys())
        writer.writeheader()
        writer.writerows(manifest)
    (OUT / "RAW_EVIDENCE.txt").write_text(
        "The 1,350 raw .sca/.vec/.vci files are retained at "
        "EmergencyNavigation/results/raw/. This package includes their sizes and SHA-256 "
        "hashes in results/raw_evidence_manifest.csv. The 360 primary and 90 waiting-control run event logs, "
        "processed CSVs, graphs, source, and reproduction instructions are included here. "
        "Earlier evidence is retained separately in EmergencyNavigation/archive_20261005_400m_telemetry20/ "
        "and EmergencyNavigation/archive_raw_20261001_650m/.\n", encoding="utf-8")
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(OUT.parent))
    print(f"Packaged {len(manifest)} raw evidence hashes; {ZIP}")


if __name__ == "__main__":
    main()
