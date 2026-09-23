#!/usr/bin/env python3
"""
Generate SHA-256 checksums for all final deliverables:
- processed CSV tables (including graph_plot_data.csv)
- verification CSV tables (response_time_verification.csv, event_timeline_verification.csv)
- audit_report.json
- publication graphs (36 density graphs)
- visual evidence screenshots
- root markdown files (README.md, PROJECT_SPEC.md, AGENTS.md, progress.md)
- docs/*.md
"""
from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TARGETS: list[Path] = [
    # Processed and sidecar CSVs
    REPO_ROOT / "results" / "processed" / "individual_runs-batch.csv",
    REPO_ROOT / "results" / "processed" / "summary-batch.csv",
    REPO_ROOT / "results" / "processed" / "paired_comparisons.csv",
    REPO_ROOT / "results" / "processed" / "fallback_validation.csv",
    REPO_ROOT / "results" / "processed" / "graph_plot_data.csv",

    # Verification tables and audit report
    REPO_ROOT / "artifacts" / "response_time_verification.csv",
    REPO_ROOT / "artifacts" / "event_timeline_verification.csv",
    REPO_ROOT / "artifacts" / "audit_report.json",

    # Root documentation files
    REPO_ROOT / "README.md",
    REPO_ROOT / "PROJECT_SPEC.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "progress.md",
]

# docs/*.md
TARGETS.extend(sorted((REPO_ROOT / "docs").glob("*.md")))

# Generated publication graphs (36 files in results/graphs/)
TARGETS.extend(sorted((REPO_ROOT / "results" / "graphs").glob("*.png")))

# Final visual evidence screenshots
TARGETS.extend(sorted((REPO_ROOT / "artifacts" / "screenshots").glob("*.png")))

OUTPUT_FILE = REPO_ROOT / "artifacts" / "checksums.sha256"


def generate_checksums() -> int:
    lines: list[str] = []
    missing: list[str] = []
    for target in TARGETS:
        if not target.exists():
            missing.append(target.relative_to(REPO_ROOT).as_posix())
            continue
        hasher = hashlib.sha256()
        with open(target, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        rel_path = target.relative_to(REPO_ROOT).as_posix()
        digest = hasher.hexdigest()
        lines.append(f"{digest}  {rel_path}")

    if missing:
        print(f"Warning: {len(missing)} target files missing: {missing}")

    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Computed {len(lines)} SHA-256 checksums -> {OUTPUT_FILE}")
    return len(lines)


if __name__ == "__main__":
    generate_checksums()
