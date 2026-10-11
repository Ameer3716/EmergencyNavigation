"""Share byte-identical completed result copies; preserve every path and byte.

Run inside WSL. No active run files, logs, model inputs or canonical raw data
are removed. Replacing a verified duplicate with a hard link saves one copy.
"""
import argparse
import filecmp
import json
import os
import time
from pathlib import Path

CONTEXTS = ('ordinary', 'obstruction')
PHASES = ('tuning', 'report')

def deduplicate(root):
    saved = count = 0
    for completed in sorted((root/'results/raw').glob('*.vci')):
        stem = completed.stem
        config, density, seed = stem.rsplit('-', 2)
        source_dir = root/'simulations/batch'/f'{density}-{seed}'/config/'results'
        raw = [completed.with_suffix('.'+ext) for ext in ('sca', 'vec', 'vci')]
        if not all(p.is_file() and p.stat().st_size > 0 for p in raw):
            continue
        for canonical in raw:
            duplicate = source_dir/('Batch-#0'+canonical.suffix)
            if not duplicate.is_file():
                continue
            first, second = canonical.stat(), duplicate.stat()
            if first.st_dev != second.st_dev or first.st_ino == second.st_ino:
                continue
            if first.st_size != second.st_size or not filecmp.cmp(canonical, duplicate, shallow=False):
                continue
            # Recheck both files after comparison; never replace a changing file.
            signature = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
            if signature(canonical.stat()) != signature(first) or signature(duplicate.stat()) != signature(second):
                continue
            temporary = duplicate.with_name(duplicate.name+'.dedup-link')
            if temporary.exists():
                continue
            os.link(canonical, temporary)
            try:
                os.replace(temporary, duplicate)
            finally:
                if temporary.exists():
                    temporary.unlink()
            count += 1
            saved += second.st_size
    return count, saved

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    project = Path('/mnt/d/Codex/EmergencyNavigation')
    output = project/'artifacts/policy_validation/storage_savings.json'
    total_count = total_saved = 0
    if output.exists():
        prior = json.loads(output.read_text())
        total_count = prior['duplicate_files_shared']
        total_saved = prior['duplicate_bytes_eliminated']
    while True:
        for phase in PHASES:
            for context in CONTEXTS:
                root = Path(f'/home/opp_env/policy_{phase}_{context}_20261010').resolve()
                if root.is_dir():
                    count, saved = deduplicate(root)
                    total_count += count
                    total_saved += saved
        record = dict(checked_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                      duplicate_files_shared=total_count,
                      duplicate_bytes_eliminated=total_saved,
                      method='Byte comparison, then hard link; all paths and bytes retained')
        output.write_text(json.dumps(record, indent=2)+'\n')
        print(json.dumps(record), flush=True)
        state = json.loads((project/'artifacts/policy_validation/status.json').read_text())
        if not args.watch or state['phase'] != 'reported_matrices':
            break
        time.sleep(60)

if __name__ == '__main__':
    main()
