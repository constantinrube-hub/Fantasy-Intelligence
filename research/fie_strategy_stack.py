#!/usr/bin/env python3
"""FIE V9.8-V10.4 market, league-value and actionable research consumers.

This module deliberately sits *after* the football projection layers.  ADP is never an
input into a football prediction.  The stack consumes existing M9/V9.7 season boards,
league profiles, immutable Sleeper market snapshots and V9.6 current overlays to answer:

* what does this production mean in this exact league?
* where does FIE disagree with the market?
* what can we act on now?

Every new consumer is research/shadow-only in this release.  Missing historical market
or availability evidence produces an explicit blocked state rather than hindsight data.
"""
from __future__ import annotations

import gzip
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

BUILD = "V10.4-STRATEGY-STACK-SHADOW-2"
OFFENSE = ("QB", "RB", "WR", "TE")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite(v) -> Optional[float]:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def load_json(path: str | Path, default=None):
    p = Path(path)
    if not p.is_file():
        return {} if default is None else default
    return json.loads(p.read_text(encoding="utf-8"))


def normalize_pos(v: Any) -> str:
    x = str(v or "").upper().strip()
    return {"DEF":"DST","D/ST":"DST"}.get(x, x)


def normalize_player_id(v: Any) -> str:
    """Normalize CSV/JSON player identifiers to a stable string join key.

    Pandas may infer Sleeper numeric IDs from CSV as int64 while immutable JSON
    market snapshots preserve them as strings.  Canonical IDs can also arrive as
    numeric-looking values.  Missing values stay empty and spreadsheet-style
    ``12345.0`` values are normalized back to ``12345``.
    """
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    s = str(v).strip()
    if not s or s.lower() in {"nan", "none", "<na>"}:
        return ""
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    return s


def load_market_rows(path: str | Path) -> List[dict]:
    p = Path(path); rows = []
    if not p.is_file(): return rows
    opener = gzip.open if p.suffix == ".gz" else open
    with opener(p, "rt", encoding="utf-8") as h:
        for line in h:
            if line.strip(): rows.append(json.loads(line))
    return rows


def market_snapshot_paths(root: str | Path, season: int) -> List[Path]:
    base = Path(root) / str(season)
    return sorted(base.glob("season_market_*.jsonl.gz")) if base.is_dir() else []


def market_movement(root: str | Path, season: int, adp_key: str) -> Tuple[pd.DataFrame, dict]:
    """Prospective ADP movement from immutable daily snapshots.

    No synthetic ADP distribution is created from a single mean.  When fewer than two
    snapshots exist, movement is explicitly unavailable.
    """
    paths = market_snapshot_paths(root, season)
    frames = []
    for p in paths:
        daym = re.search(r"season_market_(\d{4}-\d{2}-\d{2})", p.name)
        if not daym: continue
        day = daym.group(1)
        for r in load_market_rows(p):
            adp = finite((r.get("adp") or {}).get(adp_key))
            if adp is None or not (0 < adp < 999): continue
            frames.append({"market_as_of":day,"canonical_player_id":r.get("canonical_player_id"),
                           "sleeper_id":r.get("sleeper_id"),"market_player_key":str(r.get("canonical_player_id") or ("sleeper:"+str(r.get("sleeper_id") or ""))),"full_name":r.get("full_name"),
                           "position_model":normalize_pos(r.get("position_model")),"market_adp":adp})
    df = pd.DataFrame(frames)
    meta = {"snapshot_count":len(paths),"status":"ok" if len(paths)>=2 else "blocked_need_two_daily_snapshots",
            "adp_distribution_available":False,"reason":"daily means support trend, not pick-distribution probability"}
    if df.empty:
        return df, meta
    df["market_as_of"] = pd.to_datetime(df.market_as_of, errors="coerce")
    rows=[]
    for pid,g in df[df.market_player_key.astype(str).ne("sleeper:")].groupby("market_player_key", dropna=False):
        g=g.sort_values("market_as_of"); latest=g.iloc[-1]; earliest=g.iloc[0]
        def nearest(days: int):
            cutoff=latest.market_as_of-pd.Timedelta(days=days); q=g[g.market_as_of<=cutoff]
            return q.iloc[-1] if not q.empty else earliest
        r7=nearest(7); r21=nearest(21)
        rows.append({"market_player_key":pid,"canonical_player_id":latest.canonical_player_id,"sleeper_id":latest.sleeper_id,"full_name":latest.full_name,
                     "position_model":latest.position_model,"market_adp":float(latest.market_adp),
                     "opening_adp":float(earliest.market_adp),
                     "adp_change_from_open":float(earliest.market_adp-latest.market_adp),
                     "adp_change_7d":float(r7.market_adp-latest.market_adp),
                     "adp_change_21d":float(r21.market_adp-latest.market_adp),
                     "market_snapshot_count":int(len(g)),"latest_market_as_of":str(latest.market_as_of.date())})
    return pd.DataFrame(rows), meta


def adp_outcome_curves(market_root: str | Path, player_week: pd.DataFrame, adp_key: str,
                       verified_snapshot_index: Optional[dict] = None, bin_width: int = 12) -> Tuple[pd.DataFrame, dict]:
    """Historical ADP -> outcome curves using only explicitly verified preseason snapshots.

    The current repository has strong immutable capture semantics prospectively, but old
    season-market files are not automatically presumed to be pre-kickoff evidence.  A
    verified index maps season -> snapshot path.  Without >=3 historical seasons this
    project stays blocked instead of reconstructing hindsight ADP.
    """
    verified_snapshot_index = verified_snapshot_index or {}
    actual = player_week.copy()
    if "position_model" not in actual and "position" in actual: actual["position_model"] = actual.position
    req={"season","canonical_player_id","position_model","fantasy_points"}
    if not req.issubset(actual.columns):
        return pd.DataFrame(), {"status":"blocked_actual_outcomes_missing_columns","seasons":0}
    season_actual=actual.groupby(["season","canonical_player_id","position_model"],as_index=False).agg(
        actual_points=("fantasy_points","sum"), actual_ppg=("fantasy_points","mean"), games=("fantasy_points","count"))
    season_actual["actual_position_rank"]=season_actual.groupby(["season","position_model"]).actual_points.rank(method="min",ascending=False)
    panels=[]
    for sy,path in sorted(verified_snapshot_index.items()):
        p=Path(path)
        if not p.is_absolute(): p=Path(market_root)/str(path)
        if not p.is_file(): continue
        for r in load_market_rows(p):
            adp=finite((r.get("adp") or {}).get(adp_key)); cid=str(r.get("canonical_player_id") or "")
            if adp is None or not cid: continue
            panels.append({"season":int(sy),"canonical_player_id":cid,"position_model":normalize_pos(r.get("position_model")),"market_adp":adp})
    m=pd.DataFrame(panels)
    seasons=sorted(m.season.unique()) if not m.empty else []
    if len(seasons)<3:
        return pd.DataFrame(), {"status":"blocked_insufficient_verified_historical_market","seasons":len(seasons),
                                "required_seasons":3,"prospective_collection_active":True}
    z=m.merge(season_actual,on=["season","canonical_player_id","position_model"],how="inner")
    if z.empty:
        return pd.DataFrame(), {"status":"blocked_market_actual_identity_join_empty","seasons":len(seasons)}
    z["adp_bin_low"]=(np.floor((z.market_adp-1)/bin_width)*bin_width+1).astype(int)
    z["adp_bin_high"]=z.adp_bin_low+bin_width-1
    z["top12"]=(z.actual_position_rank<=12).astype(float); z["top24"]=(z.actual_position_rank<=24).astype(float)
    curves=z.groupby(["position_model","adp_bin_low","adp_bin_high"],as_index=False).agg(
        n=("actual_points","size"), expected_points=("actual_points","mean"), median_points=("actual_points","median"),
        expected_ppg=("actual_ppg","mean"), top12_rate=("top12","mean"), top24_rate=("top24","mean"))
    return curves, {"status":"diagnostic_historical_curve","seasons":len(seasons),"rows":len(z),"production_activation":False}


def _league_payload(profile: dict) -> dict:
    for candidate in [profile.get("sleeper",{}).get("league"), profile.get("league"), profile]:
        if isinstance(candidate,dict) and candidate: return candidate
    return {}


def league_structure(profile: dict) -> dict:
    league=_league_payload(profile)
    teams=int(league.get("total_rosters") or profile.get("total_rosters") or profile.get("team_count") or 12)
    roster_positions=league.get("roster_positions") or profile.get("roster_positions") or []
    counts=Counter(normalize_pos(x) for x in roster_positions)
    fixed={p:int(counts.get(p,0)) for p in OFFENSE}
    flex=int(sum(counts.get(x,0) for x in ["FLEX","W/R/T","RB/WR/TE","WRRB_FLEX","REC_FLEX"]))
    superflex=int(sum(counts.get(x,0) for x in ["SUPER_FLEX","SUPERFLEX","Q/W/R/T","OP"]))
    bench=int(counts.get("BN",0)+counts.get("BENCH",0))
    return {"teams":teams,"roster_positions":list(roster_positions),"fixed_starters_per_team":fixed,
            "flex_per_team":flex,"superflex_per_team":superflex,"bench_per_team":bench}


def _projection_col(board: pd.DataFrame) -> pd.Series:
    prod=pd.to_numeric(board.get("fie_production_mean"),errors="coerce") if "fie_production_mean" in board else pd.Series(np.nan,index=board.index)
    diag=pd.to_numeric(board.get("fie_diagnostic_mean"),errors="coerce") if "fie_diagnostic_mean" in board else pd.Series(np.nan,index=board.index)
    base=pd.to_numeric(board.get("fie_season_mean"),errors="coerce") if "fie_season_mean" in board else pd.Series(np.nan,index=board.index)
    return prod.where(prod.notna(),diag.where(diag.notna(),base))


def replacement_levels(board: pd.DataFrame, profile: dict) -> Tuple[Dict[str,float],dict]:
    """League-specific starter replacement using fixed slots then flex slots.

    No global QB12/RB24 constants are used.  Fixed starters are allocated first across
    the league; FLEX/SUPER_FLEX slots then consume the highest remaining projected
    eligible players.  The marginal selected player at each position defines the
    starter-replacement point estimate used for VORP.
    """
    s=league_structure(profile); d=board.copy(); d["position_model"]=d.position_model.map(normalize_pos)
    d["_proj"]=_projection_col(d); d=d[d.position_model.isin(OFFENSE)&d._proj.notna()].copy()
    d=d.sort_values("_proj",ascending=False); selected=set(); sel_by_pos=defaultdict(list)
    for pos,n_per in s["fixed_starters_per_team"].items():
        n=s["teams"]*n_per
        q=d[(d.position_model.eq(pos))&(~d.index.isin(selected))].head(n)
        selected.update(q.index); sel_by_pos[pos].extend(q._proj.tolist())
    for _ in range(s["teams"]*s["flex_per_team"]):
        q=d[(~d.index.isin(selected))&d.position_model.isin(["RB","WR","TE"])].head(1)
        if q.empty: break
        i=q.index[0]; selected.add(i); sel_by_pos[str(q.iloc[0].position_model)].append(float(q.iloc[0]._proj))
    for _ in range(s["teams"]*s["superflex_per_team"]):
        q=d[(~d.index.isin(selected))&d.position_model.isin(OFFENSE)].head(1)
        if q.empty: break
        i=q.index[0]; selected.add(i); sel_by_pos[str(q.iloc[0].position_model)].append(float(q.iloc[0]._proj))
    repl={}
    for pos in OFFENSE:
        vals=sel_by_pos.get(pos,[])
        if vals: repl[pos]=float(min(vals))
        else:
            q=d[d.position_model.eq(pos)]
            repl[pos]=float(q._proj.quantile(.25)) if not q.empty else 0.0
    return repl,{**s,"selected_starters":len(selected),"replacement_method":"fixed_slots_then_flex_marginal_starter"}


def _curve_lookup(curves: pd.DataFrame, pos: str, adp: Optional[float]) -> dict:
    if curves is None or curves.empty or adp is None: return {}
    q=curves[curves.position_model.astype(str).eq(pos)]
    if q.empty:return {}
    exact=q[(q.adp_bin_low<=adp)&(q.adp_bin_high>=adp)]
    if exact.empty:
        q=q.assign(_dist=np.minimum(abs(q.adp_bin_low-adp),abs(q.adp_bin_high-adp))); exact=q.nsmallest(1,"_dist")
    r=exact.iloc[0]
    return {k:finite(r.get(k)) for k in ["expected_points","median_points","expected_ppg","top12_rate","top24_rate","n"]}


def build_league_value_board(board: pd.DataFrame, profile: dict, movement: Optional[pd.DataFrame]=None,
                             curves: Optional[pd.DataFrame]=None) -> Tuple[pd.DataFrame,dict]:
    d=board.copy(); d["position_model"]=d.position_model.map(normalize_pos); d["fie_value_projection"]=_projection_col(d)
    repl,structure=replacement_levels(d,profile)
    d["replacement_points"]=d.position_model.map(repl); d["fie_vorp"]=d.fie_value_projection-d.replacement_points
    if movement is not None and not movement.empty:
        metrics=["adp_change_from_open","adp_change_7d","adp_change_21d","market_snapshot_count","latest_market_as_of"]
        # Prefer canonical identity.  Scheduled market capture may not have a derived
        # identity table, so fall back to Sleeper ID without collapsing all null IDs.
        if "canonical_player_id" in d and "canonical_player_id" in movement:
            d["_canonical_join_key"] = d["canonical_player_id"].map(normalize_player_id)
            mc=movement[["canonical_player_id"]+metrics].copy()
            mc["_canonical_join_key"] = mc["canonical_player_id"].map(normalize_player_id)
            mc=mc[mc._canonical_join_key.ne("")].drop_duplicates("_canonical_join_key").drop(columns=["canonical_player_id"])
            if not mc.empty:
                d=d.merge(mc,on="_canonical_join_key",how="left")
            else:
                for c in metrics: d[c]=np.nan
        else:
            for c in metrics: d[c]=np.nan
        if "sleeper_id" in d and "sleeper_id" in movement:
            d["_sleeper_join_key"] = d["sleeper_id"].map(normalize_player_id)
            ms=movement[["sleeper_id"]+metrics].copy()
            ms["_sleeper_join_key"] = ms["sleeper_id"].map(normalize_player_id)
            ms=ms[ms._sleeper_join_key.ne("")].drop_duplicates("_sleeper_join_key").drop(columns=["sleeper_id"])
            tmp=d[["_sleeper_join_key"]].merge(ms,on="_sleeper_join_key",how="left",suffixes=("","_sid"))
            for c in metrics:
                if c not in d: d[c]=np.nan
                d[c]=d[c].where(pd.to_numeric(d[c],errors="coerce").notna() if c!="latest_market_as_of" else d[c].notna(), tmp[c])
        d=d.drop(columns=[c for c in ["_canonical_join_key","_sleeper_join_key"] if c in d.columns])
    else:
        for c in ["adp_change_from_open","adp_change_7d","adp_change_21d","market_snapshot_count","latest_market_as_of"]: d[c]=np.nan
    market_expect=[]
    for r in d.itertuples(index=False):
        info=_curve_lookup(curves, str(getattr(r,"position_model")), finite(getattr(r,"market_adp",None)))
        market_expect.append(info)
    d["adp_implied_expected_points"]=[x.get("expected_points") for x in market_expect]
    d["adp_implied_top12_rate"]=[x.get("top12_rate") for x in market_expect]
    d["point_edge_vs_adp_history"]=d.fie_value_projection-pd.to_numeric(d.adp_implied_expected_points,errors="coerce")
    d["fie_value_position_rank"]=d.groupby("position_model").fie_value_projection.rank(method="min",ascending=False)
    if "market_position_rank" not in d:
        d["market_position_rank"]=d.groupby("position_model").market_adp.rank(method="min",ascending=True)
    d["rank_edge"]=pd.to_numeric(d.market_position_rank,errors="coerce")-pd.to_numeric(d.fie_value_position_rank,errors="coerce")
    # Keep components separate until historical research validates a combined score.
    d["market_edge_status"]="component_only_not_composite"
    d["value_label"]=np.select([
        d.rank_edge>=18,d.rank_edge>=8,d.rank_edge<=-18,d.rank_edge<=-8],
        ["STRONG_VALUE","VALUE","STRONG_FADE","OVERPRICED"], default="FAIR")
    d.loc[d.fie_value_projection.isna(),"value_label"]="UNAVAILABLE"
    meta={"build":BUILD,"status":"complete_research_only","league_structure":structure,"replacement_points":repl,
          "composite_outlier_score_enabled":False,"reason":"component weights require historical ADP validation",
          "football_projection_uses_adp":False,"runtime_projection_modified":False}
    return d,meta


def draft_actions(value_board: pd.DataFrame, current_pick: Optional[int]=None, next_pick: Optional[int]=None) -> pd.DataFrame:
    d=value_board.copy(); out=[]
    for r in d.to_dict("records"):
        edge=finite(r.get("rank_edge")); adp=finite(r.get("market_adp")); action="NO_SIGNAL"; reason="insufficient_market_edge"
        if edge is not None:
            if edge<=-10: action="AVOID_AT_MARKET"; reason="market_price_materially_above_fie_value"
            elif edge>=10:
                action="VALUE_TARGET"; reason="fie_value_materially_above_market_rank"
                if current_pick is not None and next_pick is not None and adp is not None:
                    if adp <= next_pick:
                        action="DRAFT_NOW_MARKET_MEAN"; reason="value_edge_and_mean_adp_before_next_pick"
                    elif adp > next_pick+10:
                        action="WAIT_MARKET_MEAN_ONLY"; reason="value_edge_but_mean_adp_well_after_next_pick"
        r["draft_action"]=action; r["draft_action_reason"]=reason
        r["availability_probability"]=None
        r["availability_probability_status"]="blocked_no_empirical_pick_distribution"
        out.append(r)
    return pd.DataFrame(out)


def injury_redistribution(current: dict) -> dict:
    """Current diagnostic role redistribution; never a trained injury bonus.

    OUT/IR/DOUBTFUL players create a lost-role pool.  The pool is distributed to same-
    team, same-position teammates in proportion to their observed current role.  This is
    intentionally a decision aid until prospective pregame availability history exists.
    """
    players=current.get("players") or []; rows=[]
    def feat(row,key):
        for src in [row.get("current_features") or {}, row]:
            x=finite(src.get(key))
            if x is not None:return x
        return None
    by=defaultdict(list)
    for p in players:
        team=str(p.get("team") or ""); pos=normalize_pos(p.get("position_model") or p.get("position"))
        if team and pos in OFFENSE: by[(team,pos)].append(p)
    for (team,pos),g in by.items():
        unavailable=[]
        for p in g:
            status=str(p.get("injury_status") or p.get("status") or "").upper()
            if status in {"OUT","IR","PUP","DOUBTFUL"}: unavailable.append(p)
        if not unavailable: continue
        keys=["carry_share_prior4","target_share_prior4","offense_snap_share_prior4","snap_share_prior4"]
        for injured in unavailable:
            for key in keys:
                lost=feat(injured,key)
                if lost is None or lost<=0: continue
                peers=[p for p in g if p is not injured and str(p.get("injury_status") or p.get("status") or "").upper() not in {"OUT","IR","PUP","DOUBTFUL"}]
                weights=np.array([max(0.0,feat(p,key) or 0.0) for p in peers],dtype=float)
                if not len(peers): continue
                if weights.sum()<=0: weights=np.ones(len(peers))
                weights=weights/weights.sum()
                for peer,w in zip(peers,weights):
                    rows.append({"team":team,"position":pos,"injured_player_id":injured.get("canonical_player_id"),
                                 "beneficiary_player_id":peer.get("canonical_player_id"),"role_metric":key,
                                 "lost_role":lost,"diagnostic_redistributed_role":float(lost*w),
                                 "status":"diagnostic_current_only"})
    return {"status":"diagnostic_current_only" if rows else "no_unavailable_role_pool","rows":rows,
            "production_activation":False,"historical_training_used":False,
            "reason":"prospective pregame availability history required before promotion"}


def actionable_findings(value_board: pd.DataFrame, current: Optional[dict]=None) -> dict:
    findings=[]
    d=value_board.copy()
    for r in d.to_dict("records"):
        label=str(r.get("value_label") or "")
        if label in {"STRONG_VALUE","VALUE","STRONG_FADE","OVERPRICED"}:
            findings.append({"surface":"DRAFT","player_id":r.get("canonical_player_id"),"player":r.get("full_name"),
                             "action":"TARGET" if "VALUE" in label else "FADE","priority":"HIGH" if "STRONG" in label else "MEDIUM",
                             "reason_codes":["MARKET_RANK_EDGE","LEAGUE_SPECIFIC_VORP"],
                             "evidence":{"market_adp":finite(r.get("market_adp")),"rank_edge":finite(r.get("rank_edge")),
                                         "fie_vorp":finite(r.get("fie_vorp")),"adp_change_7d":finite(r.get("adp_change_7d"))},
                             "confidence":finite(r.get("confidence") or r.get("diagnostic_confidence")),"status":"research_only"})
    if current:
        overlay=(current.get("v96_runtime") or {}).get("players") or {}
        index={str(p.get("canonical_player_id")):p for p in current.get("players") or [] if p.get("canonical_player_id")}
        for pid,info in overlay.items():
            p=index.get(str(pid),{}); hz=info.get("horizons") or {}; weekly=info.get("weekly") or {}
            b=finite((hz.get("breakout") or {}).get("prediction")); ros=finite((hz.get("rest_of_season") or {}).get("prediction"))
            delta=finite(weekly.get("delta"))
            if (b is not None and b>=.65) or (delta is not None and delta>=1.5):
                findings.append({"surface":"IN_SEASON","player_id":pid,"player":p.get("full_name"),"action":"BREAKOUT_WATCH",
                                 "priority":"HIGH" if (b or 0)>=.75 else "MEDIUM",
                                 "reason_codes":["V96_BREAKOUT" if b is not None else "V96_WEEKLY_RESIDUAL"],
                                 "evidence":{"breakout_probability":b,"weekly_delta":delta,"ros_prediction":ros},
                                 "confidence":None,"status":"research_only"})
    priority={"HIGH":0,"MEDIUM":1,"LOW":2}
    findings=sorted(findings,key=lambda x:(priority.get(x.get("priority"),9),str(x.get("player") or "")))
    return {"build":BUILD,"generated_at":now(),"status":"complete_research_only","finding_count":len(findings),
            "governance":{"auto_activation":False,"runtime_projection_modified":False,"adp_enters_football_model":False},
            "findings":findings}



def verified_market_panel(market_root: str | Path, player_week: pd.DataFrame, adp_key: str, verified_snapshot_index: dict) -> pd.DataFrame:
    """Build a time-safe market-mistake panel from verified preseason snapshots.

    Feature rows come only from season-1; outcomes come from the market season.  This
    makes the panel suitable for recurring-market-mistake research without leaking the
    target season's role into preseason hypotheses.
    """
    if not verified_snapshot_index: return pd.DataFrame()
    d=player_week.copy()
    if "position_model" not in d and "position" in d: d["position_model"]=d.position
    req={"season","canonical_player_id","position_model","fantasy_points"}
    if not req.issubset(d.columns): return pd.DataFrame()
    signals={
        "prev_carry_share": ["carry_share","carry_share_prior4"],
        "prev_target_share": ["target_share","target_share_prior4"],
        "prev_qb_rush_share": ["qb_rush_share","qb_rush_share_prior4"],
        "prev_qb_pass_share": ["qb_pass_attempt_share","qb_pass_attempt_share_prior4"],
        "prev_inside5_share": ["inside_5_carry_share","inside_5_carry_share_prior4"],
        "prev_backfield_competition": ["backfield_competition_index","backfield_competition_index_prior4","backfield_competitor_count"],
        "prev_snap_share": ["offense_snap_share","snap_share","offense_snap_share_prior4","snap_share_prior4"],
    }
    def first(names):
        for c in names:
            if c in d and pd.to_numeric(d[c],errors="coerce").notna().any(): return c
        return None
    aggs={"prev_fantasy_ppg":("fantasy_points","mean")}
    for out,names in signals.items():
        c=first(names)
        if c: aggs[out]=(c,"mean")
    prof=d.groupby(["season","canonical_player_id","position_model"],as_index=False).agg(**aggs)
    actual=d.groupby(["season","canonical_player_id","position_model"],as_index=False).agg(actual_points=("fantasy_points","sum"),actual_ppg=("fantasy_points","mean"))
    actual["actual_position_rank"]=actual.groupby(["season","position_model"]).actual_points.rank(method="min",ascending=False)
    rows=[]
    for sy,path in sorted(verified_snapshot_index.items()):
        p=Path(path)
        if not p.is_absolute(): p=Path(market_root)/str(path)
        if not p.is_file(): continue
        for r in load_market_rows(p):
            cid=str(r.get("canonical_player_id") or ""); adp=finite((r.get("adp") or {}).get(adp_key)); pos=normalize_pos(r.get("position_model"))
            if cid and adp is not None and pos in OFFENSE: rows.append({"season":int(sy),"canonical_player_id":cid,"position_model":pos,"market_adp":adp})
    m=pd.DataFrame(rows)
    if m.empty:return m
    m["market_position_rank"]=m.groupby(["season","position_model"]).market_adp.rank(method="min",ascending=True)
    prev=prof.copy(); prev["season"]=prev.season.astype(int)+1
    return m.merge(prev,on=["season","canonical_player_id","position_model"],how="left").merge(actual,on=["season","canonical_player_id","position_model"],how="inner")


def _bh_fdr(pvalues: List[float]) -> List[float]:
    if not pvalues:return []
    p=np.asarray(pvalues,float); order=np.argsort(p); q=np.empty(len(p)); prev=1.0
    for rank_i in range(len(p)-1,-1,-1):
        idx=order[rank_i]; rank=rank_i+1; val=min(prev,p[idx]*len(p)/rank); q[idx]=val; prev=val
    return q.tolist()


def _perm_pvalue(a: np.ndarray, b: np.ndarray, seed: int = 104, reps: int = 4000) -> float:
    a=np.asarray(a,float); b=np.asarray(b,float); a=a[np.isfinite(a)]; b=b[np.isfinite(b)]
    if len(a)<8 or len(b)<8:return 1.0
    observed=abs(float(a.mean()-b.mean())); joined=np.concatenate([a,b]); rng=np.random.default_rng(seed); hits=0
    for _ in range(reps):
        q=rng.permutation(joined); diff=abs(float(q[:len(a)].mean()-q[len(a):].mean())); hits += diff>=observed-1e-12
    return (hits+1)/(reps+1)

def market_mistake_research(curves: pd.DataFrame, historical_panel: Optional[pd.DataFrame]=None) -> dict:
    """Test predefined, mechanism-based ADP mistake hypotheses with BH-FDR."""
    names=["RB_high_carry_and_target_role","RB_weak_backfield_competition","RB_goal_line_role",
           "WR_high_target_share_low_prior_scoring","TE_high_target_participation","QB_rushing_role","QB_pass_volume_role"]
    if historical_panel is None or historical_panel.empty:
        return {"status":"blocked_insufficient_verified_historical_market_panel","hypotheses":names,
                "multiple_testing":"BH_FDR","activation":False}
    d=historical_panel.copy(); d["adp_rank_error"]=pd.to_numeric(d.market_position_rank,errors="coerce")-pd.to_numeric(d.actual_position_rank,errors="coerce")
    # Quantiles are computed within historical season/position, so thresholds adapt to
    # era and position rather than hard-coding today's usage levels into old seasons.
    for c in ["prev_carry_share","prev_target_share","prev_inside5_share","prev_backfield_competition","prev_qb_rush_share","prev_qb_pass_share","prev_fantasy_ppg"]:
        if c in d:
            d[c+"_pct"]=d.groupby(["season","position_model"])[c].rank(pct=True,method="average")
    tests=[]
    defs={
      "RB_high_carry_and_target_role": lambda x:(x.position_model.eq("RB")&(x.get("prev_carry_share_pct",0)>=.70)&(x.get("prev_target_share_pct",0)>=.60)),
      "RB_weak_backfield_competition": lambda x:(x.position_model.eq("RB")&(x.get("prev_backfield_competition_pct",1)<=.30)),
      "RB_goal_line_role": lambda x:(x.position_model.eq("RB")&(x.get("prev_inside5_share_pct",0)>=.70)),
      "WR_high_target_share_low_prior_scoring": lambda x:(x.position_model.eq("WR")&(x.get("prev_target_share_pct",0)>=.70)&(x.get("prev_fantasy_ppg_pct",1)<=.50)),
      "TE_high_target_participation": lambda x:(x.position_model.eq("TE")&(x.get("prev_target_share_pct",0)>=.70)),
      "QB_rushing_role": lambda x:(x.position_model.eq("QB")&(x.get("prev_qb_rush_share_pct",0)>=.70)),
      "QB_pass_volume_role": lambda x:(x.position_model.eq("QB")&(x.get("prev_qb_pass_share_pct",0)>=.70)),
    }
    for i,(name,fn) in enumerate(defs.items()):
        try: mask=pd.Series(fn(d),index=d.index).fillna(False).astype(bool)
        except Exception: mask=pd.Series(False,index=d.index)
        sig=d.loc[mask,"adp_rank_error"].dropna().to_numpy(float)
        # Control only within same position and broad ADP neighborhood to reduce the
        # obvious bias that early and late picks have different possible rank errors.
        positions=set(d.loc[mask,"position_model"].astype(str)); control=d[d.position_model.astype(str).isin(positions)&~mask].copy()
        if mask.any():
            lo=float(d.loc[mask,"market_adp"].quantile(.10))-18; hi=float(d.loc[mask,"market_adp"].quantile(.90))+18
            control=control[(control.market_adp>=lo)&(control.market_adp<=hi)]
        con=control.adp_rank_error.dropna().to_numpy(float); p=_perm_pvalue(sig,con,seed=104+i)
        tests.append({"hypothesis":name,"n_signal":int(len(sig)),"n_control":int(len(con)),
                      "mean_rank_outperformance_signal":float(np.mean(sig)) if len(sig) else None,
                      "mean_rank_outperformance_control":float(np.mean(con)) if len(con) else None,
                      "incremental_rank_outperformance":float(np.mean(sig)-np.mean(con)) if len(sig) and len(con) else None,"p_value":p})
    q=_bh_fdr([x["p_value"] for x in tests])
    for r,qq in zip(tests,q): r["q_value"]=qq; r["robust_candidate"]=bool(r["n_signal"]>=25 and r["incremental_rank_outperformance"] is not None and r["incremental_rank_outperformance"]>0 and qq<=.10)
    return {"status":"complete_research_only","hypotheses":tests,"multiple_testing":"BH_FDR_q<=0.10","activation":False,
            "validated_candidates":[r["hypothesis"] for r in tests if r["robust_candidate"]]}

def strategy_summary(value_board: pd.DataFrame, movement_meta: dict, curve_meta: dict, preseason_v2: Optional[dict]=None) -> dict:
    counts=value_board.value_label.value_counts(dropna=False).to_dict() if not value_board.empty and "value_label" in value_board else {}
    return {"build":BUILD,"generated_at":now(),"status":"complete_research_only",
            "phases":{"A_preseason_v2":(preseason_v2 or {}).get("status","not_supplied"),
                      "B_market_movement":movement_meta.get("status"),"B_adp_outcomes":curve_meta.get("status"),
                      "C_league_value":"complete" if not value_board.empty else "blocked",
                      "D_market_mistakes":"prospective_until_verified_history",
                      "E_draft_actions":"research_only","F_inseason_actions":"consumes_v96_when_available",
                      "G_injury":"diagnostic_current_only","G_matchup":"reuse_M8_component_research_contract",
                      "H_actionable_findings":"research_only"},
            "value_labels":{str(k):int(v) for k,v in counts.items()},
            "governance":{"auto_activation":False,"canonical_projections_modified":False,
                          "football_model_uses_adp":False,"next_season_runtime_enabled":False,
                          "historical_hindsight_adp_allowed":False}}
