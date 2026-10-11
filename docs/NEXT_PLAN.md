# Next experiment plan - fixed before new runs

Date: 11 October 2026. Starting commit: e3178f2. Results requested by 13 October.
Baseline: FogCloudAStarAdvance. Proposed: MistDynamicFogFallback.

## Questions and hypotheses

1. Equal dynamic routing may explain most of the fixed-obstruction gain.
   FogCloudDynamicAdvance isolates remote routing from local Mist routing while
   keeping received observations, A* costs, review thresholds and signal policy
   equal. A small or negative Mist advantage will be reported.
2. More demand can create ordinary queues, but trip count alone does not prove
   congestion. Verify physical queues and EV motion using SUMO FCD on pilot seeds.
3. Random incident locations and timing test whether one fixed blockage has
   exaggerated generality. Incidents may occur too late to affect some EVs;
   those scheduled runs remain in the results.
4. Signal waiting may remain zero or improve inconclusively. No artificial wait,
   seed selection, minimum outcome or effect-size acceptance test is permitted.

## Configuration set and invariants

Use all seven existing configurations plus FogCloudDynamicAdvance. The existing
low/medium/high ordinary and fixed-obstruction evidence remains unchanged.
NoPreemptionBaseline is an auxiliary control displayed only for signal waiting.
The main matched contrast and the dynamic-Fog ablation both use 250 m / 20 s
advance requests, 5 s review, 10% replacement improvement, 5% slow-route
improvement, two slow samples, and 30 s minimum reroute gap. Dynamic Fog uses
actual RouteRequest/RouteReply radio traffic and the existing Fog processing
delay. Initial cloud routing remains the existing baseline implementation.
Dynamic reviews target the geographically nearest existing Fog RSU, using known
infrastructure positions. Requests and replies still traverse the radio model;
out-of-range/lost requests are recorded, not bypassed through a direct call.
Remote replies that no longer contain the current edge are logged and rejected;
unanswered requests expire at the next review, without slowing or holding the EV.

Existing Mist periodic reviews compute synchronously inside their review event;
they do not schedule the initial Mist processing delay again. Dynamic Fog
reviews include the existing remote service delay and actual radio delivery.
This preserved modeling assumption limits the ablation: it compares the modeled
frameworks, including initial routing, review service and communication, rather
than isolating physical OBU CPU performance. Candidate and remaining costs both
exclude the current edge, matching the existing A* search convention.

Retain watchdog 500 ms, telemetry validation 0 ms, metric poll 100 ms, SUMO
update 500 ms, radio range 400 m, speed cap 13.9 m/s and all signal safety rules.
Eight existing reported Mist seeds retain the 900 ms controlled injected fault.
No new organic-fallback claim is made. All inputs for each seed/scenario are
identical across configurations. Existing scheduled start stop is retained.

## Demand pilot and predeclared escalation

Pilot seeds: every seed 101 through 110, for both 400 and 600 background trips.
Pilot configurations: matched baseline, proposed, dynamic Fog (60 runs).
Before that pilot, one ordinary high-density regression on held-out seed 102
checks proposed behavior against the preserved reference-tuning run. This is a
model-equivalence check, not another tuning candidate or reported seed.
Begin with 360 s departure windows: periods 0.9 and 0.6 s. If there is no
meaningful physical congestion, repeat all pilot seeds/configurations with a
common 120 s departure window (periods 0.3 and 0.2 s). This is a peak-demand
scenario, not a speed change or a weakened baseline. The two demand levels use
the same window. A final 60 s window is allowed only if pilot timing still
permits the 24-hour budget. All unsuccessful pilots are retained and disclosed.

Physical congestion diagnostics: at 0.5 s FCD samples count normal vehicles
below 1 m/s on each external edge; disclose maximum queue, vehicle-seconds below
1 m/s, peak inserted/active count, uninserted trips and baseline response.
Confirm queues on EV corridor edges as well as elsewhere. Compare 400 versus
600 baseline response on the same pilot seeds, and old 200-trip context with
its different seed set explicitly disclosed. Report failed congestion
qualification honestly; do not label a scenario congested without evidence.
Freeze demand window and inputs before any reported demand runs. No algorithm
parameter tuning uses reported seeds. No seeds 31-60 are scheduled.

## Reported matrices

Every reported cell retains seeds 1 through 30, including non-delivery and
non-arrival. Time metrics disclose available matched pairs; failures remain
in delivery/arrival counts and are not assigned artificial times.

* Congested ordinary: two frozen demand levels x eight configurations x 30
  seeds = 480 runs.
* Random incident family: existing high (200-trip) demand x eight
  configurations x 30 seeds = 240 runs. One density is used to control runtime;
  no additional low/medium random-incident cells are scheduled.
* Historical ablation: dynamic Fog only at all three original densities, in
  ordinary and the original fixed obstruction = 180 runs. Other configurations
  use preserved e3178f2 evidence; baseline/proposed source behavior must remain
  unchanged and this cross-binary provenance is disclosed and checked.

Random incidents: independent Random(20261011 + seed), shared by all
configurations. Draw an internal edge of the shortest legal EV route (exclude
start and destination), integer start time uniformly 60-150 s, and stopped
vehicle count uniformly 1-3. Place physical passenger vehicles at 40, 55, 70 m
on the selected edge, with a stop until start+160 s; use a connected continuation
from the shared network. FCD records requested and realized insertion/stop times.
An incident is not guaranteed to block the EV. Never reject weaker exposure.

## Optional algorithm improvement

Not scheduled in this deadline-limited batch. Queue/signal-aware costs require
validated, observable signal information and a separate development comparison
on 101-110 plus confirmation on 111-120. No untested cost change is adopted.
Seeds 111-120 are reserved, not part of the reported matrix.

## Runtime budget and reduction rule

Observed previous resume: 933 reported runs in approximately 3 hours at up to
96 simultaneous processes, roughly 5.2 runs/minute. Heavy-demand estimates use
one third of that throughput (about 1.7 runs/minute) plus a factor of two reserve.
900 reported + 60 initial pilot runs take approximately 9.4 hours at that rate;
reserve, build, analysis and document work yield an initial 18-23 hour estimate.
This is an estimate, not a completion guarantee. FCD is sampled every 0.5 s;
completed raw outputs share storage and FCD is gzip-compressed by SUMO.
New reported vector files are retained losslessly as .vec.gz with their
uncompressed SHA-256 and byte count in each run manifest. This avoids filling
the SSD; scalar and index files remain directly readable. Decompress a vector
before opening it with an OMNeT++ vector viewer. Metric extraction uses raw
scalars and logs and is unchanged. Completed pilot vectors may be archived in
the same way after all pilot workers finish. No evidence is discarded.

Re-estimate from pilot wall times and active process-seconds, including setup,
all additional pilots and at least two hours for processing/document QA. If the
estimate exceeds 24 hours, drop the 400-trip reported cell first (240 runs),
then reduce historical ablation to original high density in both contexts
(60 instead of 180 runs). Never reduce seeds per cell. Record any reduction in
a dated amendment before the affected reported runs begin. If the reduced
scope still exceeds budget, report the estimate and remaining scope explicitly
rather than silently exceeding the limit or dropping scheduled runs.

## Metrics and inference

Primary seven: PDR, NRL, EM throughput bit/s, EM end-to-end ms, route decision
ms, EV response s, signal waiting s. Secondary: full stops, time below 1 m/s,
mean EV journey speed, green approach share, matched background time loss at
900 s, route changes/reviews, Fog requests, fallback count/rate and latency ms.
Mean speed is related to journey time and cannot alone establish requirement C.
Background time loss uses shared observed normal IDs, with counts/unfinished
trips disclosed; it is not a pure causal measure of preemption harm.

Report paired proposed-minus-baseline differences, baseline/proposed means,
percent change (undefined when baseline zero), 95% intervals and sample sizes.
Use fixed-seed paired percentile bootstrap intervals for all waiting contrasts
and means; the same paired resampling draws for each metric. Report normal and
controlled-fault cohorts separately as well as the full scheduled matrix.
Requirement B uses the prior 20% reference without accepting/rejecting data on
effect size. Requirement C evaluates full stops, green approach share and
background loss; all wins and losses are shown. Requirement D needs lower
waiting with an interval below zero and a positive proposed mean; zero remains
zero when measured. No claims of continuous phase precision beyond 500 ms.

## Deliverables and validation

Add deterministic scenario/draw and dynamic-Fog tests; build a frozen binary.
Reuse existing scalar, mobility, summary and plotting pipeline functions.
Generate new per-run/summary/paired/bootstrap/plot CSVs, graphs, audit evidence,
and docs from raw files only. Check exact seed matrices, shared input hashes,
source/binary provenance, fixed safety parameters and FCD exposure. Keep ordinary,
congested demand, fixed incidents and random incidents separate. Update Word
with matched results first, graphs and plain explanations; preserve historical
Word evidence separately. Render and inspect the final Word document.
Generate docs/SUPERVISOR_SUMMARY.md (one page) with A-D per scenario and explicit
unmet requirements. Final A-D tables include every density/scenario, values,
percent change, paired 95% intervals and sample counts. Success never gates data
acceptance.
