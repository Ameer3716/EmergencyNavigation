#!/usr/bin/env python3
"""
Automated thesis deliverable test suite.
Validates:
  1. Dynamic A* high-density seed 22 behavior (legitimate congestion detour).
  2. FogCloud medium-density seed 14 preemption behavior (IEEE 802.11p packet loss).
  3. PDR Wilson confidence intervals (bounded [0, 1]).
  4. 450-run batch matrix completeness and delivery failure partitions.
  5. Fallback evidence fields and watchdog validation.
  6. Absence of stale legacy graphs in results/graphs/ root.
  7. Absence of stale documentation phrases across all Markdown files.
"""

import csv
import glob
import os
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestThesisDeliverable(unittest.TestCase):

    def test_01_dynamic_seed22_behavior(self):
        """Verify Dynamic A* High Seed 22 reroute logs and root cause."""
        for cfg in ["MistDynamicAStar", "MistDynamicFogFallback"]:
            log_path = REPO_ROOT / "artifacts" / "logs" / "batch" / f"routing-{cfg}-high-seed22.csv"
            self.assertTrue(log_path.exists(), f"Log file missing: {log_path}")

            with open(log_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertGreater(len(rows), 0, f"No rows in {log_path}")
            # Verify initial route applied
            initial_row = next(r for r in rows if r["action"] == "applied" and r["reason"] == "initial")
            self.assertAlmostEqual(float(initial_row["time"]), 66.8456, places=2)
            initial_route = initial_row["selectedEdges"].split("|")
            self.assertEqual(initial_route, ["A0A1", "A1B1", "B1C1", "C1C2", "C2D2", "D2D3"])

            # Verify reroute occurred due to low speed
            reroute_row = next((r for r in rows if r["action"] == "applied" and r["reason"] == "low_speed"), None)
            self.assertIsNotNone(reroute_row, f"Expected low_speed reroute event in {cfg} seed 22")
            self.assertAlmostEqual(float(reroute_row["time"]), 131.846, places=2)
            self.assertEqual(reroute_row["currentEdge"], "B1B2")

            # Check the detour route
            detour_route = reroute_row["selectedEdges"].split("|")
            self.assertIn("B2B3", detour_route, "Reroute should take macro-detour via B2B3")
            self.assertIn("B3C3", detour_route, "Reroute should take macro-detour via B3C3")
            self.assertIn("C3C2", detour_route, "Reroute should take macro-detour via C3C2")

            # Check processed individual run data
            indiv_path = REPO_ROOT / "results" / "processed" / "individual_runs-batch.csv"
            with open(indiv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                match = next(r for r in reader if r["configuration"] == cfg and r["density"] == "high" and int(r["seed"]) == 22)
                self.assertAlmostEqual(float(match["ev_response_s"]), 187.5, places=1)
                self.assertAlmostEqual(float(match["ev_distance_m"]), 2376.445, places=2)

    def test_02_fogcloud_medium_seed14_preemption(self):
        """Verify FogCloud Medium Seed 14 traffic light waiting behavior."""
        tl_log = REPO_ROOT / "artifacts" / "logs" / "batch" / "traffic-light-FogCloudAStar-medium-seed14.csv"
        self.assertTrue(tl_log.exists(), f"Log file missing: {tl_log}")

        with open(tl_log, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            tl_rows = list(reader)

        # Confirm that junction C2 never had a request received (dropped over IEEE 802.11p channel)
        c2_requests = [r for r in tl_rows if r["trafficLightId"] == "C2"]
        self.assertEqual(len(c2_requests), 0, "C2 preemption should have failed due to dropped packet")

        # Confirm other intersections (A1, B1, C1, D2, D3) received preemption
        preempted_lights = set(r["trafficLightId"] for r in tl_rows if r["action"] == "request_received")
        self.assertEqual(preempted_lights, {"A1", "B1", "C1", "D2", "D3"})

        # Check individual run metrics
        indiv_path = REPO_ROOT / "results" / "processed" / "individual_runs-batch.csv"
        with open(indiv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            match = next(r for r in reader if r["configuration"] == "FogCloudAStar" and r["density"] == "medium" and int(r["seed"]) == 14)
            self.assertAlmostEqual(float(match["traffic_light_wait_s"]), 17.0, places=1)
            self.assertAlmostEqual(float(match["ev_response_s"]), 164.0, places=1)

        # Check summary waiting time reduction for medium traffic: 0.586s vs 29.966s -> 98.04%
        summary_path = REPO_ROOT / "results" / "processed" / "summary-batch.csv"
        with open(summary_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            s_rows = list(reader)
            fc_med = next(r for r in s_rows if r["configuration"] == "FogCloudAStar" and r["density"] == "medium" and r["metric"] == "traffic_light_wait_s")
            base_med = next(r for r in s_rows if r["configuration"] == "NoPreemptionBaseline" and r["density"] == "medium" and r["metric"] == "traffic_light_wait_s")
            fc_wait = float(fc_med["mean"])
            base_wait = float(base_med["mean"])
            reduction = (base_wait - fc_wait) / base_wait * 100.0
            self.assertAlmostEqual(reduction, 98.04, places=1)

    def test_03_pdr_wilson_intervals(self):
        """Verify that PDR Wilson confidence intervals are bounded and match expected values."""
        summary_path = REPO_ROOT / "results" / "processed" / "summary-batch.csv"
        with open(summary_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["metric"] != "pdr":
                    continue
                pdr_mean = float(row["mean"])
                ci_lower = float(row["ci95_lower"])
                ci_upper = float(row["ci95_upper"])
                density = row["density"]

                self.assertGreaterEqual(ci_lower, 0.0, f"CI lower bound {ci_lower} < 0")
                self.assertLessEqual(ci_upper, 1.0, f"CI upper bound {ci_upper} > 1")
                self.assertLessEqual(ci_lower, pdr_mean, f"CI lower {ci_lower} > mean {pdr_mean}")
                self.assertGreaterEqual(ci_upper, pdr_mean, f"CI upper {ci_upper} < mean {pdr_mean}")

                if density in ["low", "high"]:
                    # 28 / 30
                    self.assertAlmostEqual(ci_lower, 0.787, places=2)
                    self.assertAlmostEqual(ci_upper, 0.982, places=2)
                elif density == "medium":
                    # 29 / 30
                    self.assertAlmostEqual(ci_lower, 0.833, places=2)
                    self.assertAlmostEqual(ci_upper, 0.994, places=2)

    def test_04_batch_matrix_completeness(self):
        """Verify exactly 450 runs, 5 configs, 3 densities, 30 seeds, and delivery failure partitions."""
        indiv_path = REPO_ROOT / "results" / "processed" / "individual_runs-batch.csv"
        with open(indiv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 450, f"Expected 450 rows, got {len(rows)}")

        expected_configs = {
            "FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback", "NoPreemptionBaseline"
        }
        expected_densities = {"low", "medium", "high"}
        expected_seeds = set(range(1, 31))

        seen = set()
        delivery_failures = {"low": set(), "medium": set(), "high": set()}

        for r in rows:
            key = (r["configuration"], r["density"], int(r["seed"]))
            self.assertNotIn(key, seen, f"Duplicate combination: {key}")
            seen.add(key)
            self.assertIn(r["configuration"], expected_configs)
            self.assertIn(r["density"], expected_densities)
            self.assertIn(int(r["seed"]), expected_seeds)

            if int(r["delivered_messages"]) == 0:
                delivery_failures[r["density"]].add(int(r["seed"]))

        self.assertEqual(len(seen), 450)
        self.assertEqual(delivery_failures["low"], {12, 28}, "Low density failure seeds mismatch")
        self.assertEqual(delivery_failures["medium"], {21}, "Medium density failure seeds mismatch")
        self.assertEqual(delivery_failures["high"], {13, 21}, "High density failure seeds mismatch")

    def test_05_fallback_evidence_fields(self):
        """Verify fallback validation table schema, exception fallback, and watchdog timeout fallback."""
        fallback_path = REPO_ROOT / "results" / "processed" / "fallback_validation.csv"
        self.assertTrue(fallback_path.exists(), f"Missing {fallback_path}")

        required_cols = [
            "scenario", "configuration", "density", "seed", "em_generation_time_s",
            "mist_start_s", "mist_completion_s", "scheduled_mist_duration_s", "observed_mist_duration_s",
            "watchdog_threshold_s", "watchdog_expiry_s", "mist_status", "failure_reason", "fallback_triggered",
            "fallback_trigger_type", "fallback_trigger_time_s", "fog_request_time_s",
            "fog_reception_time_s", "fog_computation_s", "communication_delay_s",
            "cloud_backhaul_s", "final_decision_time_s", "final_decision_latency_s",
            "applied_route", "supplying_tier"
        ]

        numeric_cols = [
            "em_generation_time_s", "mist_start_s", "mist_completion_s",
            "scheduled_mist_duration_s", "observed_mist_duration_s",
            "watchdog_threshold_s", "watchdog_expiry_s", "fallback_trigger_time_s",
            "fog_request_time_s", "fog_reception_time_s", "fog_computation_s",
            "communication_delay_s", "cloud_backhaul_s", "final_decision_time_s",
            "final_decision_latency_s"
        ]

        with open(fallback_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for col in required_cols:
                self.assertIn(col, fieldnames, f"Missing required column: {col}")

            rows = list(reader)
            self.assertGreaterEqual(len(rows), 87)

            # Assert strictly numeric or empty strings in numeric columns across all rows
            for idx, r in enumerate(rows):
                for col in numeric_cols:
                    val = r[col].strip()
                    if val != "":
                        try:
                            float(val)
                        except ValueError:
                            self.fail(f"Row {idx} ({r['configuration']}) column '{col}' contains non-numeric text: '{val}'")

            # Check forced failure row (immediate exception fallback)
            forced_row = next((r for r in rows if r["configuration"] == "ForcedMistFailure"), None)
            self.assertIsNotNone(forced_row, "ForcedMistFailure row missing from fallback validation")
            self.assertEqual(forced_row["fallback_triggered"], "1")
            self.assertEqual(forced_row["fallback_trigger_type"], "exception")
            self.assertEqual(forced_row["supplying_tier"], "fog")
            self.assertEqual(forced_row["mist_completion_s"], "")  # Blank on exception
            self.assertAlmostEqual(float(forced_row["watchdog_threshold_s"]), 0.8, places=2)
            self.assertAlmostEqual(float(forced_row["fog_request_time_s"]), 67.0188, places=4)
            self.assertAlmostEqual(float(forced_row["final_decision_time_s"]), 67.3436, places=4)

            # Check forced timeout row (genuine 800ms watchdog timeout fallback)
            timeout_row = next((r for r in rows if r["configuration"] == "ForcedMistTimeout"), None)
            self.assertIsNotNone(timeout_row, "ForcedMistTimeout row missing from fallback validation")
            self.assertEqual(timeout_row["fallback_triggered"], "1")
            self.assertEqual(timeout_row["fallback_trigger_type"], "timeout")
            self.assertEqual(timeout_row["supplying_tier"], "fog")
            self.assertAlmostEqual(float(timeout_row["watchdog_threshold_s"]), 0.8, places=2)
            self.assertAlmostEqual(float(timeout_row["mist_start_s"]), 67.0273, places=4)
            self.assertAlmostEqual(float(timeout_row["watchdog_expiry_s"]), 67.8273, places=4)
            self.assertAlmostEqual(float(timeout_row["fog_request_time_s"]), 67.8273, places=4)
            self.assertGreaterEqual(float(timeout_row["fog_request_time_s"]), float(timeout_row["watchdog_expiry_s"]))
            self.assertAlmostEqual(float(timeout_row["final_decision_time_s"]), 68.1540, places=4)

    def test_06_stale_graph_detection(self):
        """Verify no stale unsuffixed graphs in results/graphs/ and verify legacy/ directory."""
        legacy_names = [
            "ev_response_s.png", "pdr.png", "nrl.png", "control_bytes.png",
            "control_transmissions.png", "e2e_delay_s.png", "ev_distance_m.png",
            "ev_travel_s.png", "route_decision_s.png", "throughput_bps.png",
            "traffic_light_wait_s.png"
        ]
        graphs_dir = REPO_ROOT / "results" / "graphs"
        for name in legacy_names:
            root_graph = graphs_dir / name
            self.assertFalse(root_graph.exists(), f"Stale unsuffixed graph in root: {root_graph}")

        legacy_dir = graphs_dir / "legacy"
        self.assertTrue(legacy_dir.exists(), "legacy/ directory must exist in results/graphs/")
        for name in legacy_names:
            archived = legacy_dir / name
            self.assertTrue(archived.exists(), f"Legacy graph missing from archive: {archived}")

        # Check all 36 valid density graphs
        metrics = [
            "control_bytes", "control_transmissions", "e2e_delay_s", "ev_delay_vs_freeflow_s",
            "ev_distance_m", "ev_response_s", "ev_travel_s", "nrl", "pdr",
            "route_decision_s", "throughput_bps", "traffic_light_wait_s"
        ]
        for m in metrics:
            for d in ["low", "medium", "high"]:
                g_file = graphs_dir / f"{m}-{d}.png"
                self.assertTrue(g_file.exists(), f"Missing graph: {g_file}")
                self.assertGreater(g_file.stat().st_size, 1000, f"Graph file empty: {g_file}")

        final_graph = REPO_ROOT / "artifacts" / "screenshots" / "final-ev-response-graph.png"
        self.assertTrue(final_graph.exists(), f"Missing {final_graph}")

    def test_07_stale_documentation_phrases(self):
        """Verify documentation contains no obsolete phrases or inaccurate claims."""
        doc_files = [
            REPO_ROOT / "docs" / "EXPERIMENTS.md",
            REPO_ROOT / "docs" / "INSTALLATION.md",
            REPO_ROOT / "docs" / "METHODOLOGY.md",
            REPO_ROOT / "docs" / "VERIFICATION.md",
            REPO_ROOT / "PROJECT_SPEC.md",
            REPO_ROOT / "README.md",
            REPO_ROOT / "progress.md"
        ]

        forbidden_patterns = [
            (r"\b94\.12%\b", "Obsolete 94.12% PDR"),
            (r"\b414/450\b", "Obsolete 414/450 delivery count"),
            (r"\bn\s*=\s*16\b", "Obsolete n=16"),
            (r"\bn\s*=\s*5\b", "Obsolete n=5"),
            (r"Line 59", "Brittle Line 59 reference"),
            (r"t\s*=\s*60(?:\.0)?\s*s?\s*(?:as|is)?\s*EM generation", "t=60 as EM generation"),
            (r"zero waiting (?:across all|for all active)", "Universal 0.0s waiting claim"),
            (r"eliminated false (?:macro-)?detours across all seeds", "Universal false detour elimination claim")
        ]

        for path in doc_files:
            self.assertTrue(path.exists(), f"Doc file missing: {path}")
            content = path.read_text(encoding="utf-8")
            for pattern, desc in forbidden_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                self.assertIsNone(match, f"Found forbidden phrase '{desc}' in {path.name}: {match.group(0) if match else ''}")

    def test_08_paired_comparison_statistics(self):
        """Verify exact Student-t paired comparison statistics, Cohen's dz, and zero-variance handling."""
        paired_path = REPO_ROOT / "results" / "processed" / "paired_comparisons.csv"
        self.assertTrue(paired_path.exists(), f"Missing {paired_path}")

        required_cols = [
            "density", "config_A", "config_B", "metric", "N_scheduled", "n_pairs", "mean_A", "mean_B",
            "mean_paired_diff", "stddev_diff", "se_diff", "t_critical_95", "ci95_lower", "ci95_upper",
            "t_statistic", "p_value", "cohen_dz", "test_status"
        ]

        with open(paired_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for col in required_cols:
                self.assertIn(col, reader.fieldnames, f"Missing required column in paired_comparisons: {col}")

            rows = list(reader)
            self.assertGreater(len(rows), 0)

            for r in rows:
                if r["test_status"] == "not_applicable_zero_variance":
                    self.assertEqual(float(r["mean_paired_diff"]), 0.0)
                    self.assertEqual(float(r["stddev_diff"]), 0.0)
                    self.assertIn(r["p_value"], ["NA", "not_applicable_zero_variance"])
                else:
                    pval = float(r["p_value"])
                    self.assertGreaterEqual(pval, 0.0)
                    self.assertLessEqual(pval, 1.0)
                    # Confirm p-value is not a dummy coarse 0.5 or 0.05
                    self.assertNotEqual(r["p_value"], "0.5")
                    # Check Cohen's dz = mean_paired_diff / stddev_diff if stddev_diff > 0
                    sd_d = float(r["stddev_diff"])
                    if sd_d > 1e-12:
                        expected_dz = float(r["mean_paired_diff"]) / sd_d
                        self.assertAlmostEqual(float(r["cohen_dz"]), expected_dz, places=3)

    def test_09_response_time_verification_scalars(self):
        """Verify that response_time_verification.csv confirms 425 delivered runs PASS and 25 partition runs NA."""
        verif_path = REPO_ROOT / "artifacts" / "response_time_verification.csv"
        self.assertTrue(verif_path.exists(), f"Missing {verif_path}")

        with open(verif_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 450, f"Expected 450 total runs in matrix, got {len(rows)}")

        pass_rows = [r for r in rows if r["status"] == "PASS"]
        partition_rows = [r for r in rows if r["status"] == "NOT_APPLICABLE_NETWORK_PARTITION"]
        other_rows = [r for r in rows if r["status"] not in ("PASS", "NOT_APPLICABLE_NETWORK_PARTITION")]

        self.assertEqual(len(pass_rows), 425, f"Expected exactly 425 PASS runs, got {len(pass_rows)}")
        self.assertEqual(len(partition_rows), 25, f"Expected exactly 25 partition runs, got {len(partition_rows)}")
        self.assertEqual(len(other_rows), 0, f"Unexpected verification status rows: {other_rows}")

        # Audit assertion: Fail if any row with missing/empty arrival or calculated response is marked PASS
        for idx, r in enumerate(rows):
            arrival = r["raw_ev_arrival_s"].strip()
            resp = r["calculated_response_s"].strip()
            if arrival == "" or resp == "":
                self.assertNotEqual(r["status"], "PASS", f"Row {idx} ({r['configuration']} {r['density']} seed {r['seed']}) with missing timestamps was marked PASS!")

        # Verify all 425 PASS rows have exact formula match within 1e-4
        for r in pass_rows:
            diff = float(r["difference_s"])
            self.assertLess(abs(diff), 1e-4, f"Response time formula mismatch in {r}")

        # Verify all 25 partition rows preserve numeric EM generation time while arrival/response are empty
        for r in partition_rows:
            em_gen = r["raw_em_generation_s"].strip()
            self.assertNotEqual(em_gen, "", f"Missing EM generation time in partition row: {r}")
            self.assertGreater(float(em_gen), 60.0, f"Invalid EM generation time in partition row: {em_gen}")
            self.assertEqual(r["raw_ev_arrival_s"], "")
            self.assertEqual(r["calculated_response_s"], "")
            self.assertEqual(r["stored_response_s"], "")
            self.assertEqual(r["difference_s"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)

