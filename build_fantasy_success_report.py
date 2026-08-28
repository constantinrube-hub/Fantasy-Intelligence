#!/usr/bin/env python3
"""Generate the M7-M9 Fantasy Success rankings/report from a frozen season board."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Dict, List
import pandas as pd

LIMITS={'QB':24,'RB':36,'WR':36,'TE':24}
SLEEPERS={'QB':5,'RB':10,'WR':10,'TE':5}


def loadj(p): return json.loads(Path(p).read_text()) if p and Path(p).exists() else {}

def fmt(x,d=1):
    try:
        return f'{float(x):.{d}f}' if math.isfinite(float(x)) else '—'
    except Exception:return '—'

def position_evidence(m7:dict,pos:str)->List[str]:
    rows=[r for r in m7.get('driver_research',{}).get('driver_ranking',[]) if r.get('position')==pos]
    rows=sorted(rows,key=lambda r:r.get('position_evidence_rank',999))[:6]
    return [f"{r.get('feature')} ({r.get('family')})" for r in rows]

def matchup_evidence(m8:dict,pos:str)->List[str]:
    rows=[r for r in m8.get('matchup_validation',{}).get('aggregate',[]) if r.get('position')==pos]
    rows=sorted(rows,key=lambda r:float(r.get('mean_incremental_mae_improvement') or -999),reverse=True)
    return [f"{r.get('family')} [{r.get('status')}]" for r in rows[:4]]

def parse_contrib(raw):
    try:d=json.loads(raw or '{}')
    except Exception:return []
    return sorted(d.items(),key=lambda kv:abs(float(kv[1])),reverse=True)

def row_reason(r,m7,m8):
    parts=[]
    if str(r.projection_source).startswith('FIE'):
        c=parse_contrib(getattr(r,'driver_contributions_ppg','{}'))
        if c:
            plus=[f"{k} +{fmt(v,2)} PPG" for k,v in c if float(v)>0][:2]
            minus=[f"{k} {fmt(v,2)} PPG" for k,v in c if float(v)<0][:2]
            parts += plus+minus
    else: parts.append('market fallback: preseason FIE gate/player profile unavailable')
    if bool(getattr(r,'team_changed',False)): parts.append('team change: prior-team role features fail closed')
    gap=getattr(r,'scoring_unsupported','')
    if gap is not None and str(gap).strip() and str(gap).lower() not in {'nan','none'}:
        parts.append('scoring gaps: '+str(gap))
    if not parts:
        ev=position_evidence(m7,str(r.position_model))[:2]
        parts.extend(ev)
    return '; '.join(parts[:4])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',required=True);ap.add_argument('--m7-bundle',required=True);ap.add_argument('--m8-bundle',required=True);ap.add_argument('--m9-bundle',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args()
    df=pd.read_csv(a.board,low_memory=False);m7=loadj(a.m7_bundle);m8=loadj(a.m8_bundle);m9=loadj(a.m9_bundle)
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    for c in ['market_position_rank','fie_position_rank','rank_edge','fie_season_mean','p10','p50','p90','confidence','market_adp']:
        if c in df:df[c]=pd.to_numeric(df[c],errors='coerce')
    df['reason']=df.apply(lambda r:row_reason(r,m7,m8),axis=1)
    universe=[];sleep=[]
    for pos,lim in LIMITS.items():
        p=df[df.position_model.eq(pos)].copy().sort_values(['market_position_rank','market_adp'],na_position='last')
        top=p[p.market_position_rank<=lim].copy();universe.append(top)
        outside=p[(p.market_position_rank>lim)|p.market_position_rank.isna()].copy()
        outside=outside[outside.rank_edge.notna()].sort_values(['rank_edge','fie_position_rank'],ascending=[False,True]).head(SLEEPERS[pos]);sleep.append(outside)
    u=pd.concat(universe,ignore_index=True) if universe else pd.DataFrame();s=pd.concat(sleep,ignore_index=True) if sleep else pd.DataFrame()
    u.to_csv(out/'top_market_universe.csv',index=False);s.to_csv(out/'sleepers.csv',index=False);df.to_csv(out/'full_season_board.csv',index=False)
    biggest=u[u.rank_edge.notna()].copy();biggest['abs_edge']=biggest.rank_edge.abs();biggest=biggest[biggest.abs_edge>0].sort_values('abs_edge',ascending=False).head(30)
    lines=['# FIE Fantasy Success, M7-M9 Season Report','',
           'This report is fail-closed. A player uses the independent FIE preseason projection only when the position-level year-to-year raw-stat gate cleared, the player has a usable prior-season profile, the league scoring is replayable by the model targets, and team-transfer guardrails permit it. Otherwise the frozen Sleeper season projection remains the market fallback.','',
           '## Model status','',
           f"- M7 validated driver families: {len(m7.get('driver_research',{}).get('validated_candidate_families',[]))}",
           f"- M8 validated matchup families: {len(m8.get('matchup_validation',{}).get('validated_candidate_families',[]))}",
           f"- M8 sequential M7+M8 position specs: {', '.join((m8.get('matchup_validation',{}).get('sequential_activation',{}).get('model_specs') or {}).keys()) or 'none'}",
           f"- M9 weekly returner candidates: {', '.join(m9.get('returner_intelligence',{}).get('validated_candidates',[])) or 'none'}",
           f"- M9 season-return targets: {', '.join((m9.get('returner_intelligence',{}).get('season_projection',{}).get('model_specs') or {}).keys()) or 'none'}",
           f"- M9 preseason position specs: {', '.join((m9.get('preseason_season_projection',{}).get('model_specs') or {}).keys()) or 'none'}",'',
           '## Position-level predictive evidence','']
    for pos in LIMITS:
        lines += [f'### {pos}', '', '**M7 driver evidence:** '+(', '.join(position_evidence(m7,pos)) or 'insufficient'), '',
                  '**M8 matchup evidence:** '+(', '.join(matchup_evidence(m8,pos)) or 'insufficient'), '']
    lines += ['## Requested Sleeper market universe','']
    for pos,lim in LIMITS.items():
        top=u[u.position_model.eq(pos)].copy().sort_values(['market_position_rank','market_adp'],na_position='last')
        lines += [f'### {pos} Top {lim}', '',
                  '| Player | Sleeper rank | FIE rank | Edge | Projection | P10 | P50 | P90 | Confidence | Source | Why |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|']
        for r in top.itertuples(index=False):
            lines.append(f"| {r.full_name} | {fmt(r.market_position_rank,0)} | {fmt(r.fie_position_rank,0)} | {fmt(r.rank_edge,0)} | {fmt(r.fie_season_mean)} | {fmt(r.p10)} | {fmt(r.p50)} | {fmt(r.p90)} | {fmt(r.confidence,0)}% | {r.projection_source} | {str(r.reason).replace('|','/')} |")
        lines.append('')
    lines += ['## Largest FIE vs Sleeper ranking differences','',
              '| Player | Pos | Sleeper rank | FIE rank | Edge | Mean | P10 | P90 | Confidence | Why |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in biggest.itertuples(index=False):
        lines.append(f"| {r.full_name} | {r.position_model} | {fmt(r.market_position_rank,0)} | {fmt(r.fie_position_rank,0)} | {fmt(r.rank_edge,0)} | {fmt(r.fie_season_mean)} | {fmt(r.p10)} | {fmt(r.p90)} | {fmt(r.confidence,0)}% | {str(r.reason).replace('|','/')} |")
    lines += ['','## Sleeper candidates outside the requested market cutoffs','']
    if s.empty:lines.append('No qualified FIE-vs-market sleeper edges were available under the current gates.')
    else:
        lines += ['| Player | Pos | Sleeper rank | FIE rank | Edge | Mean | P10 | P90 | Why |','|---|---:|---:|---:|---:|---:|---:|---:|---|']
        for r in s.itertuples(index=False):lines.append(f"| {r.full_name} | {r.position_model} | {fmt(r.market_position_rank,0)} | {fmt(r.fie_position_rank,0)} | {fmt(r.rank_edge,0)} | {fmt(r.fie_season_mean)} | {fmt(r.p10)} | {fmt(r.p90)} | {str(r.reason).replace('|','/')} |")
    lines += ['','## Interpretation rules','',
              '- Positive Edge means FIE ranks the player earlier within his position than the frozen Sleeper market.',
              '- P10/P90 come from empirically calibrated historical OOS weekly residuals, not a fixed percentage around the mean.',
              '- `MARKET_FALLBACK` is not a hidden FIE opinion. It means the new independent preseason model was not eligible for that row.',
              '- M8 opponent/trench effects do not stack onto M7 merely because both validate independently. A sequential/joint gate is required before live stacking.',
              '- Individual return yards/TDs enter a FIE season projection only when the league scores them and the matching M9 season-return target has independently cleared its gate.',
              '- Individual WR-DB and blocker-rusher labels remain blocked without auditable assignment/responsibility history.']
    (out/'Fantasy_Success_Report.md').write_text('\n'.join(lines),encoding='utf-8')
    manifest={'rows':len(df),'requested_market_universe_rows':len(u),'sleepers_rows':len(s),'largest_differences_rows':len(biggest),'files':['Fantasy_Success_Report.md','top_market_universe.csv','sleepers.csv','full_season_board.csv']}
    (out/'report_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest))
if __name__=='__main__':main()
