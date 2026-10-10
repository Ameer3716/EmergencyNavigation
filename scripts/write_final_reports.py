#!/usr/bin/env python3
"""Generate documentation from the current matched experiment evidence."""
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")
DENSITIES = ("low", "medium", "high")
PRIMARY = (("pdr", "PDR", "ratio"), ("nrl", "NRL", "packets/delivery"),
           ("throughput_bps", "EM throughput", "bit/s"), ("e2e_delay_ms", "EM end-to-end delay", "ms"),
           ("route_decision_ms", "Route decision latency", "ms"), ("ev_response_s", "EV response time", "s"),
           ("traffic_light_wait_s", "EV traffic-light waiting time", "s"))
STALL_SEEDS = (4, 5, 9, 10, 13, 17, 18, 29)


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fmt(value, metric):
    return f"{float(value):.3f}" if metric in ("pdr", "throughput_bps", "ev_response_s", "traffic_light_wait_s") else f"{float(value):,.2f}"


def main():
    summary = rows(ROOT / "results/processed/summary-batch.csv")
    individual = rows(ROOT / "results/processed/individual_runs-batch.csv")
    fallback = rows(ROOT / "results/processed/fallback_validation.csv")
    cohorts = rows(ROOT / "results/processed/summary-cohorts.csv")
    if len(individual) != 450:
        raise SystemExit("Expected 360 primary runs and 90 waiting-time control runs")
    current = {(r['configuration'], r['density'], r['metric']): r for r in summary}
    cohort_map = {(r['scenario_condition'], r['configuration'], r['density'], r['metric']): r for r in cohorts}
    initial_nodes, all_nodes = [], []
    for run in individual:
        if not run['configuration'].startswith('Mist'):
            continue
        path = ROOT / f"artifacts/logs/batch/routing-{run['configuration']}-{run['density']}-seed{run['seed']}.csv"
        for event in rows(path) if path.exists() else []:
            if event['action'] in ('computed', 'evaluated'):
                all_nodes.append(int(event['expandedNodes']))
            if event['action'] == 'computed' and event['reason'] == 'initial':
                initial_nodes.append(int(event['expandedNodes']))
    counts = {d: len(ET.parse(ROOT / f"simulations/batch/{d}-seed1/normal-{d}-seed1.rou.xml").getroot().findall("vehicle")) for d in DENSITIES}
    docs = ROOT / "docs"
    methodology = '''# Methodology

## Experiment design

SUMO 1.18.0 moves vehicles on a 4 by 4 signalized grid with 48 directed road links. OMNeT++ 6.3.0 and Veins 5.3.1 simulate wireless communication through TraCI. Three RSUs use a 400 m radio neighborhood. Low, medium, and high demand generates 72, 144, and 200 background trips over 360 seconds. Trip generation count differs from the number simultaneously on the road. The collector records peak active background vehicles and unique background vehicles seen up to EV arrival.

The 30 seed labels vary randomTrips demand generation and OMNeT++ random streams. Veins launchd uses the manager's default seed -1, which selects run number zero; SUMO driving randomness therefore uses seed 0 in these runs, overriding the seed written in grid.sumocfg. Different demand seeds still produce different routes and entry edges. Driving randomness is held common rather than independently varied. Varying the SUMO driving seed would define a different experiment and is not silently applied to existing results.

The main comparison is FogCloudAStar, MistAStar, MistDynamicAStar, and MistDynamicFogFallback at three densities and 30 matched seeds (360 runs). A further 90 NoPreemptionBaseline runs use FogCloudAStar routing with signal priority disabled. This control is displayed only for traffic-light waiting time. Its other collected values remain in the individual-run CSV for transparency.

## Routing and controlled fallback tests

Mist initial processing is 300 ms plus 2 ms per expanded A* node. Telemetry validation adds 0 ms per received message. The fallback watchdog is 500 ms. Normal operation is reported separately from controlled stalls. A fixed independent random selection with Python seed 20261005 selects eight seeds: 4, 5, 9, 10, 13, 17, 18, and 29. These receive an additional 900 ms initial Mist worker stall in every Mist configuration and at every density. The other 22 seeds have no injected stall. This is an explicit fault-injection experiment; the delay is not measured OBU behavior and the fallback must not be described as organic. Fog/Cloud is unaffected by a local Mist stall. A selected seed that does not receive the EM cannot activate fallback.

Dynamic A* reads received vehicle beacons and RSU edge reports, requires at least three observed vehicles for a congestion adjustment, and schedules a review every five seconds. A review during an internal junction or without a valid remaining route can skip computation; the review metric counts logged route evaluations, not all timer firings. A replacement needs 10% lower remaining cost, or a confirmed slow edge with 5% improvement. Two slow observations and a 30-second gap help prevent route oscillation. Observed speeds are capped at the road speed limit in the cost estimate, keeping the A* free-flow heuristic admissible. Initial processing delays are modeled; periodic reviews are atomic simulation evaluations. Reviews and applied route changes are separate counts. Routing logs include candidate cost, current remaining cost, observed edge count, and the controlled stall parameter.

## Vehicle movement and signal priority

The EV is held until its first route is ready. Release uses SUMO automatic speed control, a 13.9 m/s maximum speed, and speed mode 31 so car following, acceleration, junction priority, and red-light safety checks apply. No blue-light device is used to ignore red signals.

Fog/Cloud and static Mist send a reactive priority request within 100 m or an estimated eight seconds of the next signal. Both dynamic Mist frameworks send advance requests within 250 m or an estimated 20 seconds. This allows time for the existing minimum green and clearance before arrival. Every preempting configuration may retry at five-second intervals if the EV still approaches the junction. The controller rejects duplicate requests during an active transition or hold; retries do not extend the 25-second maximum hold. This fixes the former permanent suppression of a junction after its first request, which prevented recovery from a lost request or an expired hold.

If the approach already has a compatible green, that phase is extended. Otherwise the controller uses 150 ms processing and checks the active green again before clearance. If SUMO started a new green during processing, that phase receives its full ten-second minimum before two seconds of yellow and one second of all-red clearance. Priority green also lasts at least ten seconds. Priority is released after the EV passes the junction or a 25-second maximum hold, followed by yellow and all-red before restoring the normal program. These are scenario timing assumptions, not a claim of compliance with a local traffic standard. No artificial waiting is added to the measurements. The dynamic frameworks combine live routing and advance signal requests; their journey-time comparison does not isolate A* computation from the signal policy.

The collector accumulates and logs at 100 ms. SUMO and the Veins manager still update motion every 500 ms; intervening polls reuse the last SUMO state. The finer accumulator does not claim 100 ms underlying motion accuracy. Traffic-light waiting is EV speed below 0.1 m/s within 20 m of the next signal after alert reception; it includes queue waiting near that stop line. Preparing green can also avoid braking before the stop line, so a response-time improvement need not equal the reduction in measured standstill waiting. Genuine green arrivals may have zero waiting. The separate short-notice red-signal suite checks positive waits and protected clearance; the simulator does not add a minimum wait to make a graph nonzero.

## Metrics and confidence intervals

PDR is delivered unique EMs divided by generated unique EMs. NRL is control plus EM transmissions divided by delivered EMs. EM throughput is delivered useful payload bits divided by a fixed 900-second window. The payload is 256 bytes: a successful run contributes 2048/900 = 2.27556 bit/s, and a nondelivery contributes zero. This is EM delivery throughput, not total network capacity. PDR and EM delay occur before route computation, so equal values across routing approaches can be correct.

EM end-to-end delay is generation to reception. Initial route decision latency is reception to route application. Both, and fallback decision latency, are displayed in milliseconds using high-precision raw scalars. Event, mobility, fallback and signal logs use 15 significant digits. Fog communication delay starts at the Fog request; routeWaitBeforeFog records watchdog waiting separately. For routes supplied by Fog, total initial latency equals waiting before Fog plus Fog processing, cloud backhaul and communication. EV response time is generation to arrival; EV travel and signal waiting remain in seconds. Response and decision measures require EM delivery, and NRL is undefined without a delivery. Corridor delay is travel time minus route distance/13.9 m/s, bounded at zero; it includes acceleration, turning, queuing, and signal effects.

PDR and fallback activation use Wilson score 95% intervals. Waiting and corridor delay use percentile bootstrap intervals with 10,000 resamples and fixed seed 42. Other continuous metrics use Student-t 95% intervals. Graphs show a generic [95% CI] label. Full mixed-cohort means and separate normal/stall means are both exported and plotted. Configuration colours are constant across figures. Matched-seed difference graphs show paired intervals; comparisons are exploratory and unadjusted for multiple testing. Paired comparisons use matching seeds and preserve a constant nonzero difference even when its sample variance is zero.
'''
    (docs / "METHODOLOGY.md").write_text(methodology, encoding="utf-8")
    lines = ["# Verification", "", "The experiment contains 360 primary runs plus 90 waiting-time control runs. Values below are calculated from unmodified simulation outputs.", ""]
    lines += ["## Seed variation in generated trips", "", "Trip IDs are reused as labels across seeds; different origins and destinations establish different placements.", "", "| High-density seed | First trip ID | Departure (s) | Origin edge | Destination edge |", "| --- | --- | ---: | --- | --- |"]
    for seed in (1, 4, 22):
        trip = ET.parse(ROOT / f"simulations/batch/high-seed{seed}/normal-high-seed{seed}.trips.xml").getroot().find('trip')
        lines.append(f"| {seed} | {trip.get('id')} | {trip.get('depart')} | {trip.get('from')} | {trip.get('to')} |")
    lines.append("")
    for density in DENSITIES:
        group = [r for r in individual if r['density'] == density and r['configuration'] == 'MistDynamicAStar']
        peak = [float(r['peak_active_background']) for r in group if r['peak_active_background']]
        spawned = [int(ET.parse(ROOT / f"artifacts/logs/batch/sumo-summary-MistDynamicAStar-{density}-seed{r['seed']}.xml").getroot().findall('step')[-1].get('inserted')) - 2 for r in group]
        delivered = sum(int(r['delivered_messages']) for r in group)
        lines += [f"## {density.capitalize()} traffic", "", f"Generated background vehicles: {counts[density]}. SUMO actually inserted {min(spawned)} to {max(spawned)} background vehicles across seeds. Peak simultaneous background count: {min(peak):.0f} to {max(peak):.0f}. Dynamic Mist alert deliveries: {delivered}/30.", "", "| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |", "| --- | ---: | ---: | ---: | ---: |"]
        for metric, label, unit in PRIMARY:
            cells = []
            for cfg in CONFIGS:
                r = current[cfg, density, metric]
                cells.append(f"{fmt(r['mean'], metric)} [{fmt(r['ci95_lower'], metric)}, {fmt(r['ci95_upper'], metric)}] (n={r['n']})")
            lines.append(f"| {label} ({unit}) | " + " | ".join(cells) + " |")
        baseline = current['NoPreemptionBaseline', density, 'traffic_light_wait_s']
        lines += ["", f"No-preemption waiting control: {float(baseline['mean']):.2f} s [{float(baseline['ci95_lower']):.2f}, {float(baseline['ci95_upper']):.2f}], n={baseline['n']}.", "", "### Routing and fallback", ""]
        for cfg in CONFIGS[2:]:
            g = [r for r in group] if cfg == CONFIGS[2] else [r for r in individual if r['density'] == density and r['configuration'] == cfg]
            lines.append(f"- {cfg}: {sum(int(float(r['route_reviews'])) for r in g)} reviews; {sum(int(float(r['route_changes'])) for r in g)} applied route changes.")
        f = [r for r in fallback if r['density'] == density]
        activated = [r for r in f if r['fallback_triggered'] == '1']
        lines += [f"- Fallback: {len(activated)}/30 ({len(activated)/30:.1%}); triggered seeds {', '.join(r['seed'] for r in activated) or 'none'}. These are controlled stall tests.", "", "### Normal and controlled-stall decision latency", "", "| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |", "| --- | ---: | ---: | ---: | ---: |"]
        for condition in ('normal', 'controlled_stall'):
            cells = [f"{float(cohort_map[condition,cfg,density,'route_decision_ms']['mean']):.2f} ms" for cfg in CONFIGS]
            lines.append(f"| {condition} | " + " | ".join(cells) + " |")
        costs, changes = [], []
        for r in group:
            path = ROOT / f"artifacts/logs/batch/routing-MistDynamicAStar-{density}-seed{r['seed']}.csv"
            if not path.exists():
                continue
            for e in rows(path):
                if e['action'] == 'evaluated' and float(e['estimatedCost']) > 0:
                    costs.append(float(e['estimatedCost']))
                if e['action'] == 'applied' and e['reason'] in ('low_speed','cost_improvement'):
                    changes.append(f"seed {r['seed']} at {float(e['time']):.3f} s")
        lines += ["", f"Live candidate costs: {len(costs)} evaluations, {len(set(costs))} distinct positive costs, {min(costs):.2f} to {max(costs):.2f} s. Example actual route changes: {', '.join(changes[:3]) or 'none'}.", ""]
    lines += ["## Interpreting density and approach differences", "",
              "The alert reaches the EV before route computation starts. PDR and EM end-to-end delay describe that shared radio event; EM throughput uses the same delivery count and fixed 256-byte payload. These metrics can match across routing approaches without indicating that the routing code is inactive.", "",
              "| Density | Generated background trips | Mean peak live vehicles | PDR | EM throughput (bit/s) | Mist A* response (s) | Dynamic Mist response (s) | Dynamic Mist route changes |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for density in DENSITIES:
        dynamic_runs = [r for r in individual if r['configuration'] == 'MistDynamicAStar' and r['density'] == density]
        peak_mean = sum(float(r['peak_active_background']) for r in dynamic_runs) / len(dynamic_runs)
        lines.append("| {} | {} | {:.1f} | {:.3f} | {:.3f} | {:.2f} | {:.2f} | {} |".format(
            density, counts[density], peak_mean,
            float(current['MistAStar', density, 'pdr']['mean']),
            float(current['MistAStar', density, 'throughput_bps']['mean']),
            float(current['MistAStar', density, 'ev_response_s']['mean']),
            float(current['MistDynamicAStar', density, 'ev_response_s']['mean']),
            sum(int(float(r['route_changes'])) for r in dynamic_runs)))
    lines += ["", "Density changes are present: PDR, throughput, and live vehicle counts rise with demand. Dynamic Mist is also active: it reviews live costs and applies route changes. PDR and throughput are expected to remain equal between route tiers when their common alert-delivery stage produces the same deliveries. Response means can differ after routing. Paired difference intervals, rather than overlap between independent mean intervals, determine whether matching seeds establish a difference.", "",
              "## Interpretation", "", "The confidence intervals determine whether measured response differences are convincing. Controlled stalls demonstrate recovery from a defined fault; they do not establish the fault rate in real deployment.", ""]
    lines += ["## Observed computation and watchdog margin", "",
              f"Initial A* expansions range from {min(initial_nodes)} to {max(initial_nodes)} nodes; the maximum across initial calculations and periodic reviews is {max(all_nodes)}. At 300 ms plus 2 ms per node, the latter represents {300+2*max(all_nodes)} ms of modeled processing, leaving {500-(300+2*max(all_nodes))} ms before the 500 ms watchdog. The selected 900 ms stalls are controlled fault tests, not organic overload evidence.", "",
              "Similar initial expansion counts can produce identical normal decision times across densities. Pooled latency means also depend on the delivered normal and controlled-stall samples; they should not be read as evidence that heavier traffic makes the processor faster.", ""]
    lines += ["## Matched seed differences", "", "A minus B is computed within each delivered matching seed. Negative values favour A. An interval including zero does not establish a difference. These are exploratory comparisons without multiple-testing adjustment.", "",
              "| Density | A minus B | Metric | Pairs | Mean difference | 95% CI | p value |",
              "| --- | --- | --- | ---: | ---: | --- | ---: |"]
    for r in rows(ROOT / 'results/processed/paired_comparisons.csv'):
        if r['metric'] in ('ev_response_s', 'route_decision_ms'):
            unit = 's' if r['metric'] == 'ev_response_s' else 'ms'
            lines.append(f"| {r['density']} | {r['config_A']} minus {r['config_B']} | {r['metric']} ({unit}) | {r['n_pairs']} | {float(r['mean_paired_diff']):.3f} | [{float(r['ci95_lower']):.3f}, {float(r['ci95_upper']):.3f}] | {r['p_value']} |")
    lines += ["", "The normal and controlled-stall plots and matched-seed difference plots accompany the pooled figures. Faster modeled route decisions do not automatically produce an equally large change in SUMO vehicle arrival time.", ""]
    (docs / "VERIFICATION.md").write_text("\n".join(lines), encoding="utf-8")
    # Named historical versions prevent attributing several model changes to telemetry alone.
    comparison = []
    sources = (("before_audit_fixes", "archive_20261005_before_audit_fixes/results/processed/summary-batch.csv"),
               ("400m_telemetry20", "archive_20261005_400m_telemetry20/results/processed/summary-batch.csv"),
               ("archived_650m", "archive_raw_20261001_650m/summary-batch-650m.csv"))
    client_before = 'archive_20261010_before_advance_priority/results/processed/summary-batch.csv'
    if (ROOT / client_before).exists():
        sources += (("before_advance_priority", client_before),)
    for version, source in sources:
        if not (ROOT / source).is_file():
            print(f"Historical comparison unavailable: {source}")
            continue
        old = {(r['configuration'], r['density'], r['metric']): r for r in rows(ROOT / source)}
        for cfg in CONFIGS:
            for density in DENSITIES:
                for metric, label, unit in PRIMARY:
                    old_metric = metric
                    if (cfg, density, metric) not in old and metric in ('e2e_delay_ms', 'route_decision_ms'):
                        old_metric = {'e2e_delay_ms': 'e2e_delay_s', 'route_decision_ms': 'route_decision_s'}[metric]
                    a, b = old[cfg, density, old_metric], current[cfg, density, metric]
                    before = float(a['mean']) * (1000 if old_metric.endswith('_s') and metric.endswith('_ms') else 1)
                    comparison.append(dict(comparison_version=version, historical_source=source,
                                           configuration=cfg, density=density, metric=label, unit=unit,
                                           before_mean=before, current_mean=b['mean'],
                                           change=float(b['mean'])-before, before_n=a['n'], current_n=b['n']))
    for filename, records in (("historical_headline_comparisons.csv", comparison),
                              ("before_after_headline.csv", [r for r in comparison if r['comparison_version'] == ('before_advance_priority' if (ROOT / client_before).exists() else 'before_audit_fixes')])):
        with (ROOT / 'results/processed' / filename).open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, records[0].keys()); writer.writeheader(); writer.writerows(records)
    (docs / "EXPERIMENTS.md").write_text("# Experiments\n\n" + methodology.split("## Routing and controlled fallback tests")[0].split("## Experiment design\n\n")[1] + "\nThe eight controlled stall seeds and all timing assumptions are specified in METHODOLOGY.md. Normal and stall results are in summary-cohorts.csv. NoPreemptionBaseline appears only in waiting-time summaries and graphs.\n",encoding='utf-8')
    (docs / 'PROGRESS.md').write_text('# Progress\n\nCompleted 360 primary matched runs and 90 no-preemption waiting-time controls, plus 360 separate controlled-obstruction runs and 18 separate red-signal checks. See VERIFICATION.md for measured counts and intervals, METHODOLOGY.md for model assumptions, and CLIENT_BASELINE_COMPARISON.md for direct comparisons with FogCloudAStar. The selected 20 percent response target is exceeded under obstruction at every density; ordinary traffic improves by a smaller margin. The ordinary and obstruction experiments are reported separately. Previous submission evidence is preserved in archive_20261010_before_advance_priority/. Historical comparison CSVs include only versions whose source data are available locally.\n',encoding='utf-8')
    (docs / 'INSTALLATION.md').write_text('''# Installation and reproduction

The installed stack is opp_env WSL, SUMO 1.18.0, OMNeT++ 6.3.0, and Veins 5.3.1. Run from the project directory in PowerShell:

```powershell
wsl -d opp_env -- bash /mnt/d/Codex/EmergencyNavigation/scripts/build.sh
wsl -d opp_env -- bash /mnt/d/Codex/EmergencyNavigation/scripts/run_batch_env.sh --force --jobs 4
python analysis/process_results.py --batch --require-all
python analysis/extract_fallback_evidence.py
python scripts/verify_response_times.py
python scripts/generate_final_graph.py
python scripts/write_final_reports.py
python scripts/validate_timing_evidence.py
python scripts/generate_reviewed_submission.py
python scripts/audit_batch.py
python -m unittest discover -s tests
python scripts/package_reviewed_submission.py --refresh
```

The default runner creates 450 simulations: 360 primary comparisons and 90 waiting controls. To inspect a small isolated sample, add `--seeds 1 4 --artifact-root /mnt/d/Codex/EmergencyNavigation/scratch/sample` to the runner, then process with `--batch --no-graphs --artifact-root scratch/sample`. A fresh run must not be mixed with old parameter outputs. Raw files are in results/raw, event logs and binary provenance manifests are in artifacts/logs/batch, and processed results are in results/processed.
''',encoding='utf-8')
    (ROOT / 'PROJECT_SPEC.md').write_text('# Emergency vehicle navigation project specification\n\nFour primary routing configurations are compared over 360 matched runs. NoPreemptionBaseline adds 90 runs and is displayed only for EV traffic-light waiting. The radio setting is 400 m; telemetry validation is 0 ms; the watchdog is 500 ms; metric accumulation is 100 ms with 500 ms SUMO motion updates. Eight independently selected seeds receive a 900 ms initial controlled Mist stall uniformly across all Mist approaches. Signal priority preserves a ten-second minimum green and yellow/all-red clearance. See docs/METHODOLOGY.md and docs/VERIFICATION.md.\n',encoding='utf-8')
    (ROOT / 'README.md').write_text('''# Emergency vehicle navigation simulation

SUMO, OMNeT++, and Veins model accident alert delivery and emergency vehicle routing on a signalized grid. The main comparison contains FogCloudAStar, MistAStar, MistDynamicAStar, and MistDynamicFogFallback (360 matched runs). A further 90 NoPreemptionBaseline runs appear only in the traffic-light waiting comparison.

The [Word report](docs/Emergency_Vehicle_Navigation_Final_Submission.docx) explains the system in plain English and contains every graph. The [graph guide](docs/PROCESS_AND_GRAPHS.md) displays them on GitHub. See [methodology](docs/METHODOLOGY.md), [measured verification](docs/VERIFICATION.md), and [installation](docs/INSTALLATION.md).

The watchdog is 500 ms and the telemetry delay is 0 ms. Eight of 30 seeds are explicitly labeled controlled Mist stalls, applied to every Mist approach for fairness. Normal and controlled results are available separately in results/processed/summary-cohorts.csv. Equal PDR or EM throughput can be valid because the alert precedes route computation and has a fixed payload/window.
''',encoding='utf-8')
    (ROOT / 'AGENTS.md').write_text('''# EmergencyNavigation development guide

The project uses SUMO 1.18.0, OMNeT++ 6.3.0, and Veins 5.3.1. The main comparison is four configurations times three densities times 30 seeds (360 runs), plus 90 NoPreemptionBaseline runs shown only for traffic-light waiting. The current parameters are 400 m radio range, 0 ms telemetry delay, 500 ms watchdog, and 100 ms metric accumulation with 500 ms underlying SUMO updates. Eight fixed independently sampled seeds receive 900 ms controlled initial Mist stalls in all Mist configurations. Never describe these as organic fallback or measured OBU performance.

Build with scripts/build.sh, run with scripts/run_batch_env.sh, process with analysis/process_results.py --batch --require-all, extract fallback evidence, then generate reports and audit. Previous evidence is in archive_20261005_before_audit_fixes/, archive_20261005_400m_telemetry20/ and archive_raw_20261001_650m/. Do not manually edit raw logs, result CSVs, or graphs. Regenerate them from the source pipeline. Keep the no-preemption control out of every summary and plot except traffic-light waiting.
''',encoding='utf-8')
    if (ROOT / 'results/supplemental/validation_report.json').exists():
        for name in ('METHODOLOGY.md', 'VERIFICATION.md', 'PROGRESS.md', 'EXPERIMENTS.md'):
            path = ROOT / 'docs' / name
            with path.open('a', encoding='utf-8') as handle:
                handle.write('\n## Supplementary route communication and signal validation\n\n'
                             'The seven headline metrics and the 450-run main matrix are unchanged. '
                             'Separate route-transaction metrics are derived from original raw scalars, and 18 isolated '
                             'short-notice red-signal runs validate positive waiting and safe priority transitions. '
                             'Definitions, confidence intervals, measured tables, and limitations are in '
                             '[SUPPLEMENTAL_VALIDATION.md](SUPPLEMENTAL_VALIDATION.md).\n')
        with (ROOT / 'README.md').open('a', encoding='utf-8') as handle:
            handle.write('\nSee [supplementary route communication and red-signal validation](docs/SUPPLEMENTAL_VALIDATION.md).\n')
        with (ROOT / 'AGENTS.md').open('a', encoding='utf-8') as handle:
            handle.write('\nSupplementary route transactions are derived from raw scalars by analysis/supplemental_validation.py. '
                         'The separate 18-run red-signal stress suite uses scripts/run_signal_validation.py; '
                         'its protected red phase and deliberately late priority requests must not be mixed into the main batch.\n')
        with (ROOT / 'docs/INSTALLATION.md').open('a', encoding='utf-8') as handle:
            handle.write('\n## Reproduce the isolated red signal validation\n\n'
                         'Use a fresh workspace so the main batch stays unchanged. Inside the configured WSL environment:\n\n'
                         '```bash\nbash scripts/run_batch_env.sh --signal-validation --workspace /home/opp_env/signal_validation_new\n'
                         'python analysis/supplemental_validation.py --signal-root /home/opp_env/signal_validation_new\n```\n\n'
                         'The runner uses the existing binary and matched seed trips. Retain the complete workspace and '
                         'copy it to artifacts/signal_validation before packaging. Route byte throughput is not inferred from absent packet logs.\n')
    if (ROOT / 'results/congestion_validation/validation_report.json').exists():
        for name in ('METHODOLOGY.md', 'VERIFICATION.md', 'PROGRESS.md', 'EXPERIMENTS.md'):
            with (ROOT / 'docs' / name).open('a', encoding='utf-8') as handle:
                handle.write('\n## Controlled incident and matched recovery evidence\n\n'
                             'A separate 360-run matrix uses a physical C1C2 stopped queue after initial route selection, '
                             'with the same incident input and original trips for every algorithm. FCD evidence verifies '
                             'the incident; all delivered-alert runs must reach the destination. Matched fault recovery '
                             'is also reported from the original batch. Actual tables, confidence intervals and limits '
                             'are in [REQUIREMENTS_EVIDENCE.md](REQUIREMENTS_EVIDENCE.md). Shared EM delivery metrics '
                             'keep their definitions and cannot demonstrate routing superiority. Graph labels retain '
                             'three decimals for response and waiting; SUMO motion remains sampled every 500 ms.\n')
        with (ROOT / 'README.md').open('a', encoding='utf-8') as handle:
            handle.write('\nSee [controlled incident and recovery evidence](docs/REQUIREMENTS_EVIDENCE.md).\n')
        with (ROOT / 'AGENTS.md').open('a', encoding='utf-8') as handle:
            handle.write('\nThe separate incident matrix uses scripts/run_congestion_validation.py and '
                         'analysis/congestion_validation.py. Keep incident and ordinary results separate; never '
                         'gate data acceptance on effect size or significance. Incident FCD verifies physical queues.\n')
        with (ROOT / 'docs/INSTALLATION.md').open('a', encoding='utf-8') as handle:
            handle.write('\n## Reproduce the controlled incident comparison\n\n'
                         '```bash\nbash scripts/run_batch_env.sh --congestion-validation --workspace /home/opp_env/incident_new --jobs 4\n'
                         'python analysis/congestion_validation.py --incident-root /home/opp_env/incident_new\n```\n\n'
                         'First screen seed 1 at all densities in a separate workspace with --seeds 1. '
                         'Retain the complete final workspace and copy it to artifacts/congestion_validation '
                         'before packaging. The 360-run final matrix uses all 30 seeds without selection based on outcomes.\n')
    if (ROOT / 'results/client_review/provenance.json').exists():
        for name in ('METHODOLOGY.md', 'VERIFICATION.md', 'PROGRESS.md', 'EXPERIMENTS.md'):
            with (ROOT / 'docs' / name).open('a', encoding='utf-8') as handle:
                handle.write('\n## Direct comparison with the Fog/Cloud baseline\n\n'
                             '[CLIENT_BASELINE_COMPARISON.md](CLIENT_BASELINE_COMPARISON.md) reports response, signal waiting, '
                             'decision latency, excess travel delay above free flow, and actual Fog route request counts. '
                             'The latter two are supporting metrics derived from recorded scalars, not substitutes for the seven headline metrics. '
                             'Ordinary traffic and controlled obstruction have separate matched-seed estimates and 95% intervals. '
                             'The framework comparison includes advance signal requests in dynamic Mist and reactive requests in Fog/static Mist; '
                             'both use the same safety controller and bounded retry mechanism. It is not an isolated comparison of A* computation alone.\n')
        with (ROOT / 'README.md').open('a', encoding='utf-8') as handle:
            handle.write('\nSee [direct baseline comparisons and supporting metrics](docs/CLIENT_BASELINE_COMPARISON.md).\n')
    print(f"Wrote reports from {len(individual)} measured runs")


if __name__ == '__main__':
    main()
