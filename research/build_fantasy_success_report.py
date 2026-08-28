#!/usr/bin/env python3
"""Generate the M7-M9 Fantasy Success market-comparison report.

The report separates market consensus, FIE's market-anchored diagnostic opinion, and
production-eligible independent FIE projections.  Diagnostic disagreement is not a
claim of superior accuracy.  Production activation remains governed by the existing
chronological validation gates.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import List

import pandas as pd

LIMITS = {'QB':24,'RB':36,'WR':36,'TE':24}
SLEEPERS = {'QB':5,'RB':10,'WR':10,'TE':5}

FEATURE_LABELS = {
    'prev_fantasy_ppg':'prior-season fantasy production',
    'prev__passing_yards':'prior passing-yard production',
    'prev__passing_tds':'prior passing-TD production',
    'prev__rushing_yards':'prior rushing-yard production',
    'prev__rushing_tds':'prior rushing-TD production',
    'prev__receiving_yards':'prior receiving-yard production',
    'prev__receiving_tds':'prior receiving-TD production',
    'prev__receptions':'prior reception volume',
    'prev__targets':'prior target volume',
    'prev__carries':'prior carry volume',
    'target_share_prior4':'recent target share',
    'carry_share_prior4':'recent carry share',
    'qb_pass_attempt_share_prior4':'recent QB pass-attempt role',
    'qb_rush_share_prior4':'recent QB rushing role',
    'offense_snap_share_prior4':'recent offensive snap share',
    'snap_share_prior4':'recent snap share',
    'red_zone_target_share_prior4':'recent red-zone target share',
    'red_zone_carry_share_prior4':'recent red-zone carry share',
    'inside_5_carry_share_prior4':'recent goal-line carry share',
    'opportunity_change_score_prior1':'recent role-change signal',
    'receiving_competition_index_prior4':'receiving competition',
    'receiving_competitor_count':'number of receiving competitors',
    'backfield_competition_index_prior4':'backfield competition',
    'backfield_competitor_count':'number of backfield competitors',
    'xfp_residual_prior4':'recent actual-vs-expected production gap',
    'opportunity_xfp_realized_prior4':'recent opportunity-based expected production',
    'pfr_receiving_drop_pct_prior4':'recent drop rate',
    'pfr_passing_bad_throw_pct_prior4':'recent bad-throw rate',
    'pfr_times_pressured_pct_prior4':'recent pressure rate',
    'ngs_completion_percentage_above_expectation_prior4':'completion performance vs expectation',
    'ngs_avg_separation_prior4':'recent separation',
    'ngs_percent_share_of_intended_air_yards_prior4':'recent air-yard share',
    'ngs_rush_yards_over_expected_per_att_prior4':'rushing yards over expected per attempt',
}


def loadj(p):
    return json.loads(Path(p).read_text()) if p and Path(p).exists() else {}


def fmt(x, d=1):
    try:
        return f'{float(x):.{d}f}' if math.isfinite(float(x)) else '—'
    except Exception:
        return '—'


def pct(x, d=1):
    try:
        return f'{float(x):+.{d}f}%' if math.isfinite(float(x)) else '—'
    except Exception:
        return '—'


def feature_label(name: str) -> str:
    if name in FEATURE_LABELS:
        return FEATURE_LABELS[name]
    return str(name).replace('prev__','prior ').replace('_prior4','').replace('_prior1','').replace('_',' ')


def position_evidence(m7: dict, pos: str) -> List[str]:
    rows = [r for r in m7.get('driver_research',{}).get('driver_ranking',[]) if r.get('position') == pos]
    rows = sorted(rows, key=lambda r:r.get('position_evidence_rank',999))[:6]
    return [f"{feature_label(r.get('feature'))} ({r.get('family')})" for r in rows]


def matchup_evidence(m8: dict, pos: str) -> List[str]:
    rows = [r for r in m8.get('matchup_validation',{}).get('aggregate',[]) if r.get('position') == pos]
    rows = sorted(rows, key=lambda r:float(r.get('mean_incremental_mae_improvement') or -999), reverse=True)
    return [f"{r.get('family')} [{r.get('status')}]" for r in rows[:4]]


def parse_contrib(raw):
    try: d = json.loads(raw or '{}')
    except Exception: return []
    out = []
    for k,v in d.items():
        try: out.append((k,float(v)))
        except Exception: pass
    return sorted(out, key=lambda kv:abs(kv[1]), reverse=True)


def gate_label(m9: dict, pos: str) -> str:
    a = m9.get('preseason_season_projection',{}).get('aggregate',{}).get(pos,{}) or {}
    return 'Validated preseason model' if a.get('status') == 'validated_candidate' else 'Diagnostic model'


def reason_text(r, m7, m8, m9) -> str:
    status = str(getattr(r,'diagnostic_status',''))
    if status == 'UNAVAILABLE_TEAM_CHANGE':
        return 'No diagnostic deviation: team transfer makes prior-team role profile non-portable.'
    if status == 'UNAVAILABLE_PROFILE':
        return 'No diagnostic deviation: no usable prior-season FIE profile.'
    if status == 'UNAVAILABLE_MODEL_SPEC':
        return 'No diagnostic deviation: insufficient year-to-year model specification.'
    if status == 'UNAVAILABLE_SCORING':
        return 'No diagnostic deviation: exact league-scoring replay is incomplete.'
    delta = getattr(r,'diagnostic_delta_points',None)
    try:
        direction = 'higher' if float(delta) > .05 else ('lower' if float(delta) < -.05 else 'near market')
    except Exception:
        direction = 'near market'
    c = parse_contrib(getattr(r,'diagnostic_driver_contributions_ppg','{}'))
    signals = [feature_label(k) for k,v in c[:3]]
    if signals:
        return f"FIE diagnostic is {direction}; main model signals: {', '.join(signals)}."
    ev = position_evidence(m7, str(r.position_model))[:2]
    return f"FIE diagnostic is {direction}; position evidence: {', '.join(ev) if ev else 'limited'}."


def agreement_row(p: pd.DataFrame, pos: str, m9: dict) -> dict:
    z = p[p.sleeper_market_projection.notna() & p.fie_diagnostic_mean.notna()].copy()
    comp = z[z.diagnostic_comparison_eligible.fillna(False).astype(bool)].copy() if 'diagnostic_comparison_eligible' in z else pd.DataFrame()
    if z.empty:
        return {'position':pos,'status':gate_label(m9,pos),'n':0}
    market = pd.to_numeric(z.sleeper_market_projection,errors='coerce')
    diag = pd.to_numeric(z.fie_diagnostic_mean,errors='coerce')
    delta = diag-market
    rel = delta.abs()/market.abs().where(market.abs()>1e-9)
    corr = market.rank().corr(diag.rank(), method='pearson') if len(z) >= 3 else None
    return {
        'position':pos, 'status':gate_label(m9,pos), 'n':int(len(z)), 'diagnostic_coverage':int(len(comp)),
        'avg_market':float(market.mean()), 'avg_diagnostic':float(diag.mean()), 'mean_delta':float(delta.mean()),
        'rank_correlation':float(corr) if corr is not None and math.isfinite(float(corr)) else None,
        'median_abs_delta':float(delta.abs().median()), 'p90_abs_delta':float(delta.abs().quantile(.90)),
        'within_5pct':float((rel <= .05).mean()*100) if rel.notna().any() else None,
        'over_10pct':int((rel > .10).sum()) if rel.notna().any() else 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board',required=True); ap.add_argument('--m7-bundle',required=True); ap.add_argument('--m8-bundle',required=True); ap.add_argument('--m9-bundle',required=True); ap.add_argument('--output-dir',required=True)
    a = ap.parse_args()
    df = pd.read_csv(a.board,low_memory=False); m7 = loadj(a.m7_bundle); m8 = loadj(a.m8_bundle); m9 = loadj(a.m9_bundle)
    out = Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    numeric = ['market_position_rank','fie_position_rank','rank_edge','fie_season_mean','fie_production_mean','sleeper_market_projection',
               'fie_diagnostic_mean','diagnostic_raw_mean','diagnostic_delta_points','diagnostic_delta_pct','diagnostic_position_rank','diagnostic_rank_delta',
               'diagnostic_p10','diagnostic_p50','diagnostic_p90','diagnostic_confidence','confidence','market_adp']
    for c in numeric:
        if c in df: df[c] = pd.to_numeric(df[c],errors='coerce')
    if 'diagnostic_comparison_eligible' in df:
        df['diagnostic_comparison_eligible'] = df.diagnostic_comparison_eligible.astype(str).str.lower().isin(['true','1'])
    df['reason'] = df.apply(lambda r:reason_text(r,m7,m8,m9),axis=1)
    df['evidence_status'] = df.position_model.map(lambda p:gate_label(m9,str(p)))

    universe = []; sleepers = []
    for pos, lim in LIMITS.items():
        p = df[df.position_model.eq(pos)].copy().sort_values(['market_position_rank','market_adp'],na_position='last')
        top = p[p.market_position_rank <= lim].copy(); universe.append(top)
        outside = p[((p.market_position_rank > lim) | p.market_position_rank.isna()) & p.diagnostic_comparison_eligible].copy()
        outside = outside[outside.diagnostic_rank_delta > 0].sort_values(['diagnostic_rank_delta','diagnostic_position_rank'],ascending=[False,True]).head(SLEEPERS[pos])
        sleepers.append(outside)
    u = pd.concat(universe,ignore_index=True) if universe else pd.DataFrame()
    s = pd.concat(sleepers,ignore_index=True) if sleepers else pd.DataFrame()

    comparable = u[u.diagnostic_comparison_eligible].copy() if not u.empty else pd.DataFrame()
    if not comparable.empty:
        comparable['abs_rank_delta'] = comparable.diagnostic_rank_delta.abs()
        biggest = comparable[comparable.abs_rank_delta > 0].sort_values('abs_rank_delta',ascending=False).head(30)
        positive = comparable[comparable.diagnostic_rank_delta > 0].sort_values(['diagnostic_rank_delta','diagnostic_delta_points'],ascending=[False,False]).head(20)
        negative = comparable[comparable.diagnostic_rank_delta < 0].sort_values(['diagnostic_rank_delta','diagnostic_delta_points'],ascending=[True,True]).head(20)
    else:
        biggest = positive = negative = pd.DataFrame()

    agreement = pd.DataFrame([agreement_row(df[df.position_model.eq(pos)].copy(),pos,m9) for pos in LIMITS])
    u.to_csv(out/'top_market_universe.csv',index=False)
    s.to_csv(out/'sleepers.csv',index=False)
    s.to_csv(out/'diagnostic_sleepers.csv',index=False)
    negative.to_csv(out/'diagnostic_fades.csv',index=False)
    agreement.to_csv(out/'market_agreement.csv',index=False)
    df.to_csv(out/'full_season_board.csv',index=False)

    pre = m9.get('preseason_season_projection',{}) or {}
    agg = pre.get('aggregate',{}) or {}
    validated = [p for p,v in agg.items() if (v or {}).get('status') == 'validated_candidate']
    diagnostic = [p for p in LIMITS if p not in validated]
    lines = [
        '# FIE Fantasy Success, M7-M9 Season Report','',
        '## Executive summary','',
        'This report separates **Sleeper market consensus**, a **market-anchored FIE diagnostic view**, and a **production-eligible independent FIE projection**. Diagnostic disagreement is not evidence that Sleeper is wrong. The diagnostic view is centered within each position so its average projection matches the market average; it is designed to show how FIE would redistribute the same positional fantasy-point pool across players.','',
        f"- Production-validated preseason positions: {', '.join(validated) or 'none'}",
        f"- Diagnostic-only preseason positions: {', '.join(diagnostic) or 'none'}",
        f"- M7 validated weekly driver families: {len(m7.get('driver_research',{}).get('validated_candidate_families',[]))}",
        f"- M8 validated matchup families: {len(m8.get('matchup_validation',{}).get('validated_candidate_families',[]))}",
        f"- M9 weekly returner candidates: {', '.join(m9.get('returner_intelligence',{}).get('validated_candidates',[])) or 'none'}",'',
        '## Market agreement by position','',
        '| Pos | Evidence | Players | Shadow coverage | Avg Sleeper | Avg FIE diagnostic | Mean Δ | Rank corr. | Median |Δ pts| | P90 |Δ pts| | Within ±5% | >10% |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|'
    ]
    for r in agreement.itertuples(index=False):
        lines.append(f"| {r.position} | {r.status} | {int(r.n or 0)} | {int(getattr(r,'diagnostic_coverage',0) or 0)} | {fmt(getattr(r,'avg_market',None))} | {fmt(getattr(r,'avg_diagnostic',None))} | {fmt(getattr(r,'mean_delta',None),2)} | {fmt(getattr(r,'rank_correlation',None),3)} | {fmt(getattr(r,'median_abs_delta',None))} | {fmt(getattr(r,'p90_abs_delta',None))} | {fmt(getattr(r,'within_5pct',None))}% | {int(getattr(r,'over_10pct',0) or 0)} |")

    lines += ['', '## Position-level predictive evidence','']
    for pos in LIMITS:
        g = agg.get(pos,{}) or {}
        lines += [f'### {pos}', '',
                  f"**Preseason evidence:** {gate_label(m9,pos)}; mean historical improvement {pct(100*float(g.get('mean_incremental_mae_improvement'))) if g.get('mean_incremental_mae_improvement') is not None else '—'}; 95% CI {pct(100*float(g.get('bootstrap_ci95_low'))) if g.get('bootstrap_ci95_low') is not None else '—'} to {pct(100*float(g.get('bootstrap_ci95_high'))) if g.get('bootstrap_ci95_high') is not None else '—'}.", '',
                  '**M7 driver evidence:** '+(', '.join(position_evidence(m7,pos)) or 'insufficient'), '',
                  '**M8 matchup evidence:** '+(', '.join(matchup_evidence(m8,pos)) or 'insufficient'), '']

    lines += ['## Requested Sleeper market universe','']
    for pos, lim in LIMITS.items():
        top = u[u.position_model.eq(pos)].copy().sort_values(['market_position_rank','market_adp'],na_position='last')
        lines += [f'### {pos} Top {lim}', '',
                  '| Player | Sleeper pts | FIE diagnostic | Δ pts | Δ % | Sleeper rank | FIE diag rank | Rank Δ | Independent FIE | P10 | P50 | P90 | Evidence | Why |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|']
        for r in top.itertuples(index=False):
            prod = getattr(r,'fie_production_mean',None)
            lines.append(f"| {r.full_name} | {fmt(r.sleeper_market_projection)} | {fmt(r.fie_diagnostic_mean)} | {fmt(r.diagnostic_delta_points)} | {pct(r.diagnostic_delta_pct)} | {fmt(r.market_position_rank,0)} | {fmt(r.diagnostic_position_rank,0)} | {fmt(r.diagnostic_rank_delta,0)} | {fmt(prod)} | {fmt(r.diagnostic_p10)} | {fmt(r.diagnostic_p50)} | {fmt(r.diagnostic_p90)} | {r.evidence_status} | {str(r.reason).replace('|','/')} |")
        lines.append('')

    lines += ['## Largest model-market disagreements','',
              'These are disagreements, not automatically advantages. Positive Rank Δ means FIE diagnostic ranks the player earlier; negative Rank Δ means Sleeper ranks the player earlier.','',
              '| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
    for r in biggest.itertuples(index=False):
        lines.append(f"| {r.full_name} | {r.position_model} | {fmt(r.market_position_rank,0)} | {fmt(r.diagnostic_position_rank,0)} | {fmt(r.diagnostic_rank_delta,0)} | {fmt(r.sleeper_market_projection)} | {fmt(r.fie_diagnostic_mean)} | {fmt(r.diagnostic_delta_points)} | {r.evidence_status} | {str(r.reason).replace('|','/')} |")

    lines += ['', '## Diagnostic sleeper candidates outside market cutoffs','',
              'These players are surfaced because FIE allocates them more of the position-wide fantasy-point pool than Sleeper does. For diagnostic-only positions, this is exploratory disagreement rather than evidence of superior forecasting.','']
    if s.empty:
        lines.append('No comparable positive diagnostic deviations were available outside the requested market cutoffs.')
    else:
        lines += ['| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
        for r in s.itertuples(index=False):
            lines.append(f"| {r.full_name} | {r.position_model} | {fmt(r.market_position_rank,0)} | {fmt(r.diagnostic_position_rank,0)} | {fmt(r.diagnostic_rank_delta,0)} | {fmt(r.sleeper_market_projection)} | {fmt(r.fie_diagnostic_mean)} | {fmt(r.diagnostic_delta_points)} | {r.evidence_status} | {str(r.reason).replace('|','/')} |")

    lines += ['', '## Diagnostic fades / market-higher disagreements','']
    if negative.empty:
        lines.append('No comparable negative diagnostic deviations were available.')
    else:
        lines += ['| Player | Pos | Sleeper rank | FIE diag rank | Rank Δ | Sleeper pts | FIE diagnostic | Δ pts | Evidence | Why |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
        for r in negative.itertuples(index=False):
            lines.append(f"| {r.full_name} | {r.position_model} | {fmt(r.market_position_rank,0)} | {fmt(r.diagnostic_position_rank,0)} | {fmt(r.diagnostic_rank_delta,0)} | {fmt(r.sleeper_market_projection)} | {fmt(r.fie_diagnostic_mean)} | {fmt(r.diagnostic_delta_points)} | {r.evidence_status} | {str(r.reason).replace('|','/')} |")

    lines += ['', '## Interpretation rules','',
              '- The FIE diagnostic view is centered by position. Its average fantasy-point projection equals Sleeper on the comparison population by construction.',
              '- A diagnostic deviation answers **where FIE allocates value differently**, not which model is better.',
              '- Production eligibility is separate. Only positions in the validated production model registry may replace market/fallback values in runtime consumers.',
              '- Players blocked by missing profiles, team changes, or incomplete scoring replay remain at the market baseline in the diagnostic comparison and are labelled explicitly.',
              '- P10/P50/P90 retain empirically calibrated historical OOS spread and are recentered on the diagnostic mean.',
              '- M7/M8 diagnostic feature evidence can explain football mechanisms but does not stack onto projections unless its own sequential activation gate validates.',
              '- Return production affects fantasy values only when the league scores it and the corresponding M9 return target independently validates.']

    (out/'Fantasy_Success_Report.md').write_text('\n'.join(lines),encoding='utf-8')
    manifest = {
        'rows':len(df), 'requested_market_universe_rows':len(u), 'diagnostic_sleepers_rows':len(s),
        'largest_differences_rows':len(biggest), 'diagnostic_fades_rows':len(negative),
        'validated_positions':validated, 'diagnostic_only_positions':diagnostic,
        'files':['Fantasy_Success_Report.md','top_market_universe.csv','sleepers.csv','diagnostic_sleepers.csv','diagnostic_fades.csv','market_agreement.csv','full_season_board.csv']
    }
    (out/'report_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
