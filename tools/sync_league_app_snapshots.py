#!/usr/bin/env python3
"""Copy compact fast-switch + unified research artifacts into dist.

Research integration is additive: the browser receives only readiness/rankings/
report-summary JSON, never historical prediction CSVs.
"""
from __future__ import annotations
import argparse, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def copy(src:Path,dst:Path):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def inject_script(dist:Path,src:str,tag:str):
    idx=dist/'index.html'; target=dist/src
    if not idx.exists() or not target.exists():return
    text=idx.read_text(encoding='utf-8'); html=f'<script src="{src}?v={tag}"></script>'
    if html in text:return
    marker='</body>'
    if marker not in text:raise SystemExit(f'dist index.html missing </body> for {src} injection')
    idx.write_text(text.replace(marker,html+'\n'+marker,1),encoding='utf-8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dist',default='dist');a=ap.parse_args();dist=ROOT/a.dist
    if not dist.exists():raise SystemExit(f'dist tree missing: {dist}')
    inject_script(dist,'app/core/value-calibration-guard.js','933-calibration')
    inject_script(dist,'app/core/research-report-service.js','unified-research-v1')
    inject_script(dist,'app/research-report-ui.js','unified-research-v1')
    inject_script(dist,'app/core/research-value-finder-bridge.js','unified-research-v1')
    app_data=ROOT/'data/research/app';index=app_data/'league-index.json'
    if not index.exists():print('No league app index yet; fast-switch artifacts skipped.');return
    copy(index,dist/'data/research/app/league-index.json');catalog=app_data/'player-catalog.json'
    if not catalog.exists():raise SystemExit('Shared player-catalog.json missing: cold-load fast path cannot be deployed')
    copy(catalog,dist/'data/research/app/player-catalog.json')
    count=0; research_count=0; leagues=ROOT/'data/research/leagues'
    if leagues.exists():
        for d in sorted(leagues.iterdir()):
            if not d.is_dir():continue
            for name in ('app/core.json','app/manifest.json'):
                src=d/name
                if src.exists():copy(src,dist/'data/research/leagues'/d.name/name)
            if (d/'app/core.json').exists():count+=1
            perf=d/'performance'
            if perf.is_dir():
                for pdir in perf.glob('*/research_pipeline'):
                    for name in ('readiness.json','rankings.json','report-summary.json'):
                        src=pdir/name
                        if src.exists():copy(src,dist/src.relative_to(ROOT));research_count+=1
    print(f'Synced {count} league fast-switch snapshots + shared player catalog + {research_count} compact research files into {dist.relative_to(ROOT)}')
if __name__=='__main__':main()
