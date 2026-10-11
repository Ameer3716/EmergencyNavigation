"""Predeclared dense-demand, random-incident and dynamic-Fog experiments."""
import argparse
import hashlib
import heapq
import json
import math
import random
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import run_batch as batch

def network_data(path):
    tree = ET.parse(path).getroot()
    edges = {}
    for edge in tree.findall('edge'):
        if edge.get('function') == 'internal':
            continue
        lane = edge.find('lane')
        edges[edge.get('id')] = (float(lane.get('length')), float(lane.get('speed')))
    turns = {edge: set() for edge in edges}
    for turn in tree.findall('connection'):
        if turn.get('from') in edges and turn.get('to') in edges:
            turns[turn.get('from')].add(turn.get('to'))
    return edges, turns

def shortest_route(path, start='A0A1', goal='D2D3'):
    edges, turns = network_data(path)
    network=ET.parse(path).getroot()
    junctions={j.get('id'):(float(j.get('x')),float(j.get('y'))) for j in network.findall('junction')}
    topology={e.get('id'):(e.get('from'),e.get('to')) for e in network.findall('edge') if e.get('id') in edges}
    target=junctions[topology[goal][0]]
    maximum=max(speed for length,speed in edges.values())
    def heuristic(edge):
        point=junctions[topology[edge][1]]
        return 0. if edge==goal else math.hypot(target[0]-point[0],target[1]-point[1])/maximum
    queue = [(heuristic(start), start)]
    distance = {start: 0.}
    parent = {}
    while queue:
        priority, edge = heapq.heappop(queue)
        cost=distance[edge]
        if priority > cost + heuristic(edge) + 1e-9:
            continue
        if edge == goal:
            route = [goal]
            while route[-1] != start:
                route.append(parent[route[-1]])
            return list(reversed(route))
        for following in sorted(turns[edge]):
            candidate = cost + edges[following][0] / edges[following][1]
            if candidate < distance.get(following, float('inf')) - 1e-9:
                distance[following] = candidate
                parent[following] = edge
                heapq.heappush(queue, (candidate+heuristic(following), following))
    raise ValueError('No legal EV route')

def incident_draw(network, seed):
    route = shortest_route(network)
    draw = random.Random(20261011 + seed)
    edge = draw.choice(route[1:-1])
    start = draw.randint(60, 150)
    count = draw.randint(1, 3)
    return dict(seed=seed, edge=edge, continuation=route[route.index(edge)+1],
                start_s=start, vehicles=count, stop_until_s=start+160,
                shortest_route=route, draw_seed=20261011+seed)

def incident_special(template, destination, incident):
    tree = ET.parse(template)
    routes = tree.getroot()
    kind = ET.Element('vType', id='incidentQueue', vClass='passenger', color='0.7,0,0.8')
    routes.insert(0, kind)
    routes.insert(1, ET.Element('route', id='incidentQueueRoute', edges=incident['edge']+' '+incident['continuation']))
    for index in range(incident['vehicles']):
        position = 40+15*index
        vehicle = ET.SubElement(routes, 'vehicle', id=f'incidentQueue{index}', type='incidentQueue',
                                route='incidentQueueRoute', depart=str(incident['start_s']+index),
                                departPos=str(position), departSpeed='0')
        ET.SubElement(vehicle, 'stop', lane=incident['edge']+'_0', endPos=str(position+5), until=str(incident['stop_until_s']))
    # SUMO requires chronological departure order, including the existing accident.
    vehicles = list(routes.findall('vehicle'))
    for vehicle in vehicles:
        routes.remove(vehicle)
    routes.extend(sorted(vehicles, key=lambda vehicle: (float(vehicle.get('depart')), vehicle.get('id'))))
    tree.write(destination, encoding='utf-8', xml_declaration=True)

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--context', choices=('dense','random_incident','ordinary_ablation','fixed_ablation'), required=True)
    parser.add_argument('--seeds', nargs='+', type=int, required=True)
    parser.add_argument('--densities', nargs='+', required=True)
    parser.add_argument('--configs', nargs='+', default=list(batch.NEXT_CONFIGS))
    parser.add_argument('--demand-end', type=float, default=360)
    parser.add_argument('--jobs', type=int, default=48)
    parser.add_argument('--phase', choices=('pilot','report','regression'), required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.phase == 'report' and args.seeds != list(range(1,31)):
        parser.error('Every reported cell must contain seeds 1-30')
    if args.phase == 'pilot' and args.seeds != list(range(101,111)):
        parser.error('Every demand pilot must contain seeds 101-110')
    root = args.workspace.resolve()
    source = batch.ROOT
    import fcntl
    with (root.parent/f'.{root.name}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not args.resume:
            if root.exists():
                raise SystemExit('Use --resume for an existing workspace')
            (root/'simulations/grid').mkdir(parents=True)
            (root/'scripts').mkdir()
            (root/'src').symlink_to(source/'src', target_is_directory=True)
            shutil.copy2(source/'scripts/generate_demand.py', root/'scripts')
            for path in (source/'simulations/grid').iterdir():
                if path.is_file():
                    shutil.copy2(path, root/'simulations/grid'/path.name)
            if args.context == 'fixed_ablation':
                shutil.copy2('/home/opp_env/policy_report_obstruction_20261010/simulations/grid/special.rou.xml', root/'simulations/grid/special.rou.xml')
        scenario_path = root/'scenario.json'
        specification = dict(context=args.context, phase='next_'+args.phase, source_project=str(source),
            configurations=args.configs, executed_densities=args.densities, executed_seeds=args.seeds,
            expected_runs=len(args.configs)*len(args.densities)*len(args.seeds), departure_end_s=args.demand_end,
            horizon_s=900, execution_jobs=args.jobs, plan_sha256=hashlib.sha256((source/'docs/NEXT_PLAN.md').read_bytes()).hexdigest(),
            acceptance='All scheduled cases; completeness and validity, never effect size')
        if args.resume:
            prior=json.loads(scenario_path.read_text())
            for key in ('context','configurations','executed_densities','executed_seeds','departure_end_s'):
                assert prior[key] == specification[key], key
        model = {p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted((source/'src').rglob('*')) if p.is_file() and p.suffix in ('.cc','.h','.ned','.msg') and 'out' not in p.parts}
        specification['source_model_sha256'] = model
        specification['incident_draws'] = {str(seed):incident_draw(root/'simulations/grid/grid.net.xml', seed)
                                          for seed in args.seeds} if args.context == 'random_incident' else {}
        if args.resume:
            assert prior['source_model_sha256']==model,'Frozen model changed during resume'
            specification=prior
        else:
            specification['execution_started_at']=time.time()
            shutil.copy2(source/'docs/NEXT_PLAN.md',root/'plan.snapshot.md')
            scenario_path.write_text(json.dumps(specification, indent=2)+'\n')
        original = batch.one_sumo_config
        def evidence(directory, route_name, seed, summary_path=None):
            if args.context == 'random_incident':
                incident_special(root/'simulations/grid/special.rou.xml', directory/'special.rou.xml', specification['incident_draws'][str(seed)])
            original(directory, route_name, seed, summary_path)
            if summary_path:
                path=directory/'grid.sumocfg'
                tree=ET.parse(path)
                output=tree.getroot().find('output')
                ET.SubElement(output,'tripinfo-output',value=str(summary_path).replace('sumo-summary-','tripinfo-'))
                ET.SubElement(output,'tripinfo-output.write-unfinished',value='true')
                ET.SubElement(output,'fcd-output',value=str(summary_path).replace('sumo-summary-','traffic-fcd-')+'.gz')
                ET.SubElement(output,'device.fcd.probability',value='1')
                tree.write(path,encoding='utf-8',xml_declaration=True)
        batch.one_sumo_config=evidence
        batch.ROOT=root
        batch.GRID=root/'simulations/grid'
        batch.CONFIGS=tuple(args.configs)
        started=specification.get('execution_started_at',scenario_path.stat().st_mtime)
        sys.argv=[sys.argv[0],'--seeds',*map(str,args.seeds),'--densities',*args.densities,
            '--configs',*args.configs,'--jobs',str(args.jobs),'--artifact-root',str(root),
            '--sim-time-limit','900','--demand-end',str(args.demand_end),'--resume-incomplete','--compress-vectors']
        batch.main()
        manifests=[json.loads(path.read_text()) for path in (root/'artifacts/logs/batch').glob('manifest-*.json')]
        (root/'execution.json').write_text(json.dumps(dict(wall_seconds=time.time()-started, completed_at=time.time(),
            active_process_seconds=sum(m.get('process_wall_seconds',0) for m in manifests),
            timed_runs=sum('process_wall_seconds' in m for m in manifests)),indent=2)+'\n')

if __name__ == '__main__':
    main()
