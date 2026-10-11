"""Reconstruct the pre-change response budget without modifying retained evidence."""
import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = 'time,vehicleId,edge,lanePosition,speed,distance,stopDuration,event,trafficLightWaiting,activeBackgroundVehicles'.split(',')


def main():
    rows = list(csv.DictReader((ROOT/'results/processed/individual_runs-batch.csv').open()))
    lines = ['# Diagnosis before model changes', '',
        'Baseline: FogCloudAStar. Proposed: MistDynamicFogFallback. This diagnosis uses retained ordinary results before matched-policy changes. No model code was changed to create it.', '',
        '## Where response time goes', '',
        'Response = EM delivery + route decision + release/sampling residual + measured driving. Signal standstill is part of driving, not an additional term. Queues, acceleration, turning and junction travel are also within driving; the old metric cannot causally separate them.', '',
        '| Configuration | Density | Arrivals | Response s | EM ms | Decision ms | Driving s | Signal standstill s | Release/sampling residual s | Below 1 m/s after departure s |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    missing = []
    for c in ('FogCloudAStar', 'MistDynamicFogFallback'):
        for d in ('low', 'medium', 'high'):
            group = [r for r in rows if r['configuration']==c and r['density']==d and r['ev_response_s']]
            slow = []
            for r in group:
                p=ROOT/f"artifacts/logs/batch/mobility-{c}-{d}-seed{r['seed']}.csv"
                with p.open() as handle:
                    first=handle.readline().strip().split(',')
                    handle.seek(0)
                    if first==FIELDS:
                        samples=list(csv.DictReader(handle))
                    else:
                        missing.append(p.name)
                        samples=list(csv.DictReader(handle,fieldnames=FIELDS))
                departure=min(float(s['time']) for s in samples if s['speed'] and float(s['speed'])>.1)
                slow.append(sum(.1 for s in samples if s['speed'] and float(s['time'])>=departure and float(s['speed'])<1))
            avg=lambda k:statistics.mean(float(r[k]) for r in group)
            residual=avg('ev_response_s')-avg('ev_travel_s')-(avg('route_decision_ms')+avg('e2e_delay_ms'))/1000
            lines.append(f"| {c} | {d} | {len(group)} | {avg('ev_response_s'):.3f} | {avg('e2e_delay_ms'):.3f} | {avg('route_decision_ms'):.3f} | {avg('ev_travel_s'):.3f} | {avg('traffic_light_wait_s'):.3f} | {residual:.3f} | {statistics.mean(slow):.3f} |")
    lines += ['', 'The below-1 m/s estimate uses existing 100 ms mobility rows after first movement, which repeat 500 ms SUMO states. It excludes the initial navigation hold. It is not substituted into old raw results.', '',
        'Missing-header logs encountered here (read using the declared original schema, without editing raw evidence): '+', '.join(missing)+'. Two further missing headers exist in Dynamic Mist high seed 3 and low seed 5.', '',
        '## Zero waiting: what is and is not established', '',
        'The collector only queries next TLS for speed below 0.1 m/s, then requires next-TLS distance at most 20 m. It can miss slow crawling (0.1 to 1 m/s) and stopped queues farther than 20 m. Advance requests can genuinely prepare green before arrival. The old trace has no next-TLS distance or approach phase column, so zero cannot prove every junction was reached on green. New instrumentation will log next TLS, distance, link state and controller phase on each new SUMO state, actual junction entries, and whole-route slow time. No synthetic minimum waiting will be added.', '',
        '## Physical margin', '',
        'External road travel alone takes at least 1721.6 / 13.9 = 123.856 s. This optimistic bound omits internal junctions, acceleration, route decision and EM delivery. Against the old baseline means, even a physically ideal proposal has at most 19.21%, 19.84%, and 20.71% response reduction in low, medium, and high density; real achievable margins are smaller. A 20% ordinary gain is impossible at low and medium with the unchanged trip and speed cap. An advance-policy baseline may be faster and reduce available margin. No 20% outcome is promised.', '',
        '## Scheduled start-stop caveat', '',
        'The shared special.rou.xml also defines a mandatory stop at lane position 30 m until time 65. Because the EV is held at position zero until routing completes, it reaches that stop later and SUMO still performs a stop. Initial instrumented held-out runs localize one full stop here, about 260 m before the next signal, even when signal waiting is zero. Whole-route slow time and full stops include this common scheduled stop; they must not all be attributed to traffic queues or red lights. The input is preserved for every configuration. This caveat was added after examining new instrumentation, without changing model parameters or selecting seeds.', '',
        '## Plan fixed before new reported runs', '',
        'The old dynamic frameworks use 250 m / 20 s requests; Fog/static Mist use 100 m / 8 s. Add explicit FogCloudAStarAdvance and MistAStarAdvance controls at 250 m / 20 s. Preserve the old results. Report original-policy and matched-policy comparisons separately. All signal controllers retain identical safety rules.', '',
        'Tune proposed review interval and route replacement thresholds only on seeds 101–110, then freeze settings before all reported seeds 1–30. Use the same ordinary and existing obstruction inputs for every configuration, including the speed cap and SUMO driving seed behavior. Report full stops, green crossing share, whole-route below-1 m/s time and background time loss even when proposed loses. Signal-aware routing requires reliable signal observations; no unavailable global future phase information will be invented.', '']
    (ROOT/'docs/DIAGNOSIS.md').write_text('\n'.join(lines))
    print('\n'.join(lines[:16]))


if __name__=='__main__':main()
