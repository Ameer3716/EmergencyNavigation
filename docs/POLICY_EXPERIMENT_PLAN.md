# Matched-policy experiment plan

Written after diagnosis and before any held-out or new reported run.

## Inputs and fair controls

Preserve the previous ordinary and obstruction evidence. Use new isolated workspaces. Trips, EV speed cap (13.9 m/s), safety checks, demand counts, 400 m radio range, 900 s observation window, and SUMO driving seed behavior are common across configurations. No new obstructions or longer routes are introduced. Ordinary traffic and the existing three-vehicle obstruction are separate experiments.

Retain original FogCloudAStar and MistAStar reactive controls (100 m / 8 s). Add FogCloudAStarAdvance and MistAStarAdvance at the same 250 m / 20 s settings as dynamic Mist. All use the same bounded retry and signal controller. NoPreemptionBaseline is displayed only for traffic-light waiting. The previous proposed configuration and results remain available unchanged as historical evidence.

## Held-out tuning, frozen before reported seeds

Use all ten demand seeds 101–110 at all densities in both scenarios. Compare three proposed candidates: reference (5 s review, 10% replacement, 30 s minimum gap), fast (2 s, 5%, 10 s), balanced (3 s, 8%, 20 s). All require two slow observations and 5% improvement for a slow-edge replacement. These mechanisms react to received traffic information; no route, delay or signal wait is hardcoded.

Select lowest mean EV response over the fixed 60 density/scenario/seed cells common to valid candidates. Report missing EM delivery explicitly; identical delivered sets are required to compare candidates fairly. Break a tie within 0.5 s by fewer route replacements, then retain the reference. Selection does not reject a candidate's data or any reported seed. Publish all held-out candidate outcomes, including losses. Tuning seeds have no controlled initial stall because the independently selected fault labels belong to reported seeds 1–30; this selection tunes routing under normal computation. Controlled-fault results are assessed separately in reported runs.

Freeze the selected settings and source/binary hashes. Then run every seed 1–30 at every density for seven configurations in ordinary traffic (630 runs) and six in obstruction (540 runs). Do not tune again on those results. Apply the existing independently selected 900 ms controlled stall to every Mist configuration on the same eight reported seed labels.

## Instrumentation and independent measures

Log next signal, distance, link lamp, phase index and complete state. At each observed transition off an external approach, log the associated signal phase and approach-link lamp at that SUMO sample. Crossing time is localized only within the 500 ms update interval; a crossing sampled during yellow is not labeled as a measured green. Log all samples without suppressing unfavorable observations.

Accumulate whole-route time below 1 m/s and below 0.1 m/s after first route release, excluding the deliberate initial navigation hold. Full stops count transitions below 0.1 m/s after the EV has reached at least 1 m/s, with a new stop requiring recovery to 1 m/s. Report green crossing count/share, full stops, slow time and background vehicle time loss. SUMO tripinfo includes unfinished vehicles at the common 900 s horizon; background excludes EV, accident and incident vehicles. Background time loss is not claimed as a pure causal estimate of preemption alone.

Background time-loss comparisons use the common observed normal-vehicle IDs across all compared preempting configurations for each density/seed/context. Original observed, matched and unfinished counts are also exported. Vehicles that have not entered by the horizon have no observed driving time loss and are not assigned zero. This avoids attributing cohort composition to a treatment benefit; it does not eliminate censoring at the finite horizon. The no-preemption control is excluded from this cohort definition and from every graph except signal waiting.

Before any reported runs, define a second signal measure from the extended trace: the lamp on the first arrival within 20 m of each next signal on an external edge visit. A red arrival followed by waiting and a green crossing remains a red arrival. This is distinct from the green crossing safety check, which can be equal for all approaches because every EV obeys red signals. Both measures are exported. Requirement C assesses full stops, green approach share and background time loss; crossing share remains a safety measure rather than assuming it proves an unstopped arrival.

## Statistical interpretation

Use the existing processing functions and paired Student-t 95% difference intervals, retaining all scheduled seeds and identifying delivered pairs. Keep raw scalar precision. Decision/EM/fallback delay display in ms, journey/waiting in s. Graph-visible intervals use generic [95% CI]. No outcome or significance threshold gates data acceptance. A large ordinary gain and two independent metric wins may remain unsupported; report that explicitly. Genuine zero waiting remains zero rather than injecting delay.
