#!/usr/bin/env python3
"""Copy generated compact league app snapshots into an already-built dist tree."""
from __future__ import annotations
import argparse, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def copy(src:Path,dst:Path):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)

def inject_calibration(dist:Path):
    idx=dist/'index.html'; guard=dist/'app/core/value-calibration-guard.js'
    if not idx.exists() or not guard.exists(): return
    text=idx.read_text(encoding='utf-8'); tag='<script src="app/core/value-calibration-guard.js?v=933-calibration"></script>'
    if tag in text: return
    marker='</body>'
    if marker not in text: raise SystemExit('dist index.html missing </body> for calibration injection')
    idx.write_text(text.replace(marker,tag+'\n'+marker,1),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dist',default='dist');a=ap.parse_args()
    dist=ROOT/a.dist
    if not dist.exists(): raise SystemExit(f'dist tree missing: {dist}')
    inject_calibration(dist)
    index=ROOT/'data/research/app/league-index.json'
    if not index.exists():
        print('No league app index yet; fast-switch artifacts skipped.')
        return
    copy(index,dist/'data/research/app/league-index.json')
    count=0
    leagues=ROOT/'data/research/leagues'
    if leagues.exists():
        for d in sorted(leagues.iterdir()):
            if not d.is_dir(): continue
            for name in ('app/core.json','app/manifest.json'):
                src=d/name
                if src.exists(): copy(src,dist/'data/research/leagues'/d.name/name)
            if (d/'app/core.json').exists(): count+=1
    print(f'Synced {count} league fast-switch snapshots into {dist.relative_to(ROOT)}')
if __name__=='__main__':main()
