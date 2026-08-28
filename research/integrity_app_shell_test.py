#!/usr/bin/env python3
"""Fail-closed guard for the production application shell."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REQUIRED=(
 '<title>Fantasy Intelligence Engine · Current Release</title>',
 'id="releaseMarkerV7"',
 'app/decision-ui.css',
 'app/current-snapshot-store.js',
 'app/decision-engines.js',
 'app/value-finder.js',
 'app/dst-intelligence.js',
 'app/kicker-intelligence.js',
)
FORBIDDEN=(
 '<title>Fantasy Intelligence Engine V5</title>',
 '<h1>Fantasy Intelligence Engine <span style="color:var(--accent)">V5</span></h1>',
 'V5 · Dynasty + Waivers + Start/Sit',
)

def validate_shell(path:Path,label:str)->None:
 assert path.exists(),f'{label} missing: {path}'
 text=path.read_text(encoding='utf-8')
 for marker in REQUIRED:
  assert marker in text,f'{label} missing modern marker: {marker!r}'
 for marker in FORBIDDEN:
  assert marker not in text,f'{label} contains obsolete V5 marker: {marker!r}'
 assert len(text)>500_000,f'{label} unexpectedly small/truncated: {len(text)} chars'

def shadow_files():
 return sorted({p for pat in ('index.html.txt','index.html*.txt','index.html(*)*') for p in ROOT.glob(pat) if p.is_file() and p.name!='index.html'})

def validate_source()->None:
 validate_shell(ROOT/'index.html','source index')
 bad=shadow_files()
 assert not bad,'accidental shadow index file(s) found; delete: '+', '.join(p.name for p in bad)

def validate_dist()->None:
 validate_shell(ROOT/'dist/index.html','dist index')
 assert (ROOT/'index.html').read_bytes()==(ROOT/'dist/index.html').read_bytes(), 'dist/index.html differs from root index.html'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source-only',action='store_true');ns=ap.parse_args()
 validate_source()
 if not ns.source_only: validate_dist()
 print('PASS app shell guard: modern root shell'+(' validated' if ns.source_only else ' + byte-identical dist validated'))

if __name__=='__main__':main()
