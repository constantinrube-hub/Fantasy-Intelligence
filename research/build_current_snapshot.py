#!/usr/bin/env python3
"""Build the production current-season decision snapshot for FIE V8.8-M6.

The snapshot preserves the existing V8.7-M5 browser contract, but is produced by
V8.8-M6. It is fail-closed:
- target-week realised stats are excluded;
- M4/M5 position gates must already be validated;
- empirical scoring signature must match;
- at least two completed prior games are required for FIE weekly activation;
- missing features are imputed exactly as in exported historical Ridge specs, but
  activation also requires minimum observed feature coverage;
- stale/incompatible snapshots are rejected again by Step 30 browser governance.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import requests

from fie_research import (
    DEFAULT_PPR, POSITION_METRICS, SourceManager, add_pregame_features, build_identity,
    derive_opportunity, merge_pbp_team_opportunity, normalize_position, prep_pbp_opportunity,
    prep_player_week, prep_snaps, prep_team_week, score_rows, scoring_signature,
)
from fie_m2 import add_change_signals, add_competition_features, add_position_shares, add_team_context
from fie_m3 import add_lagged_advanced, add_public_enrichment

PRODUCER_BUILD = "V8.8-M6"
M5_BUILD = "V8.7-M5"
UA = "Fantasy-Intelligence-Engine-V8.8-M6/1.0"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_json(url: str, required=True):
    try:
        r = requests.get(url, timeout=35, headers={"User-Agent": UA, "Accept": "application/json"})
        r.raise_for_status(); return r.json()
    except Exception:
        if required: raise
        return None


def load_json(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else {}


def stable_scoring(scoring: dict) -> dict:
    out = {}
    for k, v in (scoring or {}).items():
        try:
            x = float(v)
        except Exception:
            continue
        if math.isfinite(x) and x != 0:
            out[str(k)] = x
    return dict(sorted(out.items()))


def league_scoring(league_id: Optional[str], fallback: dict) -> Tuple[dict, dict]:
    if not league_id:
        return dict(fallback or DEFAULT_PPR), {"type": "research_bundle", "league_id": None}
    league = get_json(f"https://api.sleeper.app/v1/league/{league_id}")
    scoring = league.get("scoring_settings") or fallback or DEFAULT_PPR
    return scoring, {"type": "sleeper_league", "league_id": str(league_id), "league_name": league.get("name")}


def sleeper_state() -> dict:
    return get_json("https://api.sleeper.app/v1/state/nfl", required=False) or {}


def load_schedule(cache_dir: Path) -> pd.DataFrame:
    p = cache_dir / "games.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or p.stat().st_size < 1000:
        try:
            r = requests.get(GAMES_URL, timeout=45, headers={"User-Agent": UA}); r.raise_for_status(); p.write_bytes(r.content)
        except Exception:
            return pd.DataFrame()
    try:
        return pd.read_csv(p, low_memory=False)
    except Exception:
        return pd.DataFrame()


def opponent_map(schedule: pd.DataFrame, season: int, week: int) -> Dict[str, str]:
    if schedule.empty or not {"season", "week"}.issubset(schedule.columns): return {}
    s = schedule[(pd.to_numeric(schedule.season, errors="coerce") == season) & (pd.to_numeric(schedule.week, errors="coerce") == week)].copy()
    hc = next((c for c in ["home_team", "home"] if c in s.columns), None)
    ac = next((c for c in ["away_team", "away"] if c in s.columns), None)
    if not hc or not ac: return {}
    out = {}
    for r in s.itertuples(index=False):
        h = str(getattr(r, hc) or ""); a = str(getattr(r, ac) or "")
        if h and a: out[h] = a; out[a] = h
    return out


def first_kickoff_utc(schedule: pd.DataFrame, season: int, week: int) -> Optional[datetime]:
    if schedule.empty: return None
    s = schedule[(pd.to_numeric(schedule.get("season"), errors="coerce") == season) & (pd.to_numeric(schedule.get("week"), errors="coerce") == week)].copy()
    if s.empty: return None
    for c in ["gametime", "game_time", "kickoff"]:
        if c not in s.columns: continue
    # nflverse games commonly exposes a UTC datetime in gametime or a game date/time pair.
    candidates = []
    # Prefer explicit date + time combinations. Parsing a bare HH:MM string first can
    # accidentally attach today's date and would corrupt the pregame eligibility audit.
    if "game_date" in s.columns and "gametime" in s.columns:
        candidates.append(pd.to_datetime(s["game_date"].astype(str) + " " + s["gametime"].astype(str), errors="coerce", utc=True))
    if "gameday" in s.columns and "gametime" in s.columns:
        candidates.append(pd.to_datetime(s["gameday"].astype(str) + " " + s["gametime"].astype(str), errors="coerce", utc=True))
    if "game_date" in s.columns and "game_time" in s.columns:
        candidates.append(pd.to_datetime(s["game_date"].astype(str) + " " + s["game_time"].astype(str), errors="coerce", utc=True))
    # Only use a standalone gametime if it already parses as a full date-time.
    if "gametime" in s.columns:
        bare = pd.to_datetime(s["gametime"], errors="coerce", utc=True)
        if bare.notna().any() and bare.dropna().dt.year.between(season - 1, season + 1).all():
            candidates.append(bare)
    for x in candidates:
        x = x.dropna()
        if len(x):
            return x.min().to_pydatetime()
    return None


def sleeper_players() -> dict:
    rows = get_json("https://api.sleeper.app/v1/players/nfl", required=False) or {}
    return rows if isinstance(rows, dict) else {}


def sleeper_projection_rows(season: int, week: int) -> List[dict]:
    rows = get_json(f"https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular", required=False) or []
    return rows if isinstance(rows, list) else []


def score_sleeper_projection(stats: dict, scoring: dict, position: str = "") -> float:
    total = 0.0
    st = stats or {}
    for k, w in (scoring or {}).items():
        try: weight = float(w)
        except Exception: continue
        if not math.isfinite(weight) or weight == 0: continue
        if k in st:
            try: total += float(st[k]) * weight
            except Exception: pass
            continue
        # Common aliases when Sleeper emits raw names instead of scoring-key names.
        aliases = {
            "pass_yd": ["passing_yards"], "pass_td": ["passing_tds"], "pass_int": ["interceptions"],
            "pass_cmp": ["completions"], "pass_att": ["attempts", "passing_attempts"],
            "rush_yd": ["rushing_yards"], "rush_td": ["rushing_tds"], "rush_att": ["carries", "rushing_attempts"],
            "rec": ["receptions"], "rec_yd": ["receiving_yards"], "rec_td": ["receiving_tds"], "rec_tgt": ["targets"],
            "tkl_solo": ["tackles_solo"], "tkl_ast": ["tackles_with_assist", "tackles_assists"], "tkl_loss": ["tackles_for_loss"],
            "sack": ["def_sacks", "sacks"], "qb_hit": ["def_qb_hits", "qb_hits"], "int": ["def_interceptions"],
            "pass_def": ["def_pass_defended"], "ff": ["def_fumbles_forced"], "fum_rec": ["def_fumbles"], "def_td": ["def_tds"],
        }
        for a in aliases.get(k, []):
            if a in st:
                try: total += float(st[a]) * weight
                except Exception: pass
                break
        if k in {"bonus_rec_te", "rec_te"} and str(position).upper() == "TE":
            try: total += float(st.get("rec", st.get("receptions", 0))) * weight
            except Exception: pass
    return float(total)


def archive_sleeper_projection(rows: List[dict], season: int, week: int, identity: pd.DataFrame, output_root: Path, pregame_eligible: bool) -> dict:
    out = output_root / str(season) / f"week_{week:02d}.jsonl.gz"
    if out.exists():
        return {"path": str(out), "written": False, "first_write": True, "pregame_eligible": None}
    imap = {}
    if not identity.empty and {"sleeper_id", "canonical_player_id"}.issubset(identity.columns):
        for r in identity.dropna(subset=["sleeper_id", "canonical_player_id"]).itertuples(index=False):
            imap[str(r.sleeper_id)] = str(r.canonical_player_id)
    out.parent.mkdir(parents=True, exist_ok=True); captured = utc_now()
    n = 0
    with gzip.open(out, "wt", encoding="utf-8") as h:
        for r in rows:
            sid = str(r.get("player_id") or (r.get("player") or {}).get("player_id") or "")
            if not sid: continue
            rec = {"season": season, "week": week, "captured_at": captured, "pregame_eligible": bool(pregame_eligible),
                   "sleeper_id": sid, "canonical_player_id": imap.get(sid),
                   "position_model": normalize_position((r.get("player") or {}).get("position")), "stats": r.get("stats") or r}
            h.write(json.dumps(rec, separators=(",", ":")) + "\n"); n += 1
    return {"path": str(out), "written": True, "rows": n, "first_write": True, "pregame_eligible": bool(pregame_eligible)}


def current_observed_frame(season: int, target_week: int, scoring: dict, cache_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    sm = SourceManager(cache_dir)
    players = sm.load("players", required=True)
    ffids = sm.load("ff_playerids", required=False)
    identity, identity_stats = build_identity(players, ffids)
    psrc = sm.load("player_week", season, required=False)
    tsrc = sm.load("team_week", season, required=False)
    ssrc = sm.load("snaps", season, required=False)
    if psrc.empty or tsrc.empty:
        return pd.DataFrame(), pd.DataFrame(), identity, {"identity": identity_stats, "sources": [s.__dict__ for s in sm.status], "reason": "current weekly nflverse stats not yet available"}
    psrc = psrc[pd.to_numeric(psrc.get("week"), errors="coerce") < target_week].copy()
    tsrc = tsrc[pd.to_numeric(tsrc.get("week"), errors="coerce") < target_week].copy()
    if not ssrc.empty and "week" in ssrc:
        ssrc = ssrc[pd.to_numeric(ssrc.week, errors="coerce") < target_week].copy()
    if psrc.empty or tsrc.empty:
        return pd.DataFrame(), pd.DataFrame(), identity, {"identity": identity_stats, "sources": [s.__dict__ for s in sm.status], "reason": "no completed prior-week rows"}
    pw, _, scoring_support = prep_player_week([psrc], identity, scoring)
    tw = prep_team_week([tsrc])
    snaps, _ = prep_snaps([ssrc] if not ssrc.empty else [], identity)
    # PBP is optional for current runtime. It adds red-zone shares when the public file exists.
    pbp = sm.load("pbp", season, required=False)
    if not pbp.empty:
        pbp = pbp[pd.to_numeric(pbp.get("week"), errors="coerce") < target_week].copy()
        pbt, pbppl = prep_pbp_opportunity(pbp)
        tw = merge_pbp_team_opportunity(tw, pbt)
    else:
        pbppl = pd.DataFrame(); tw = merge_pbp_team_opportunity(tw, None)
    d = derive_opportunity(pw, tw, snaps, pbppl)
    metrics = sorted({m for xs in POSITION_METRICS.values() for m in xs})
    d = add_pregame_features(d, metrics)
    d, tw2 = add_team_context(d, tw)
    d = add_competition_features(d)
    d = add_position_shares(d)
    d = add_change_signals(d)
    d, enrichment = add_public_enrichment(d, identity, str(cache_dir), [season])
    d = add_lagged_advanced(d, enrichment.get("feature_columns", []))
    d = d[pd.to_numeric(d.week, errors="coerce") < target_week].copy()
    return d, tw2, identity, {
        "identity": identity_stats, "scoring_support": scoring_support, "sources": [s.__dict__ for s in sm.status],
        "advanced_coverage": enrichment.get("coverage", {}), "completed_weeks": sorted(int(x) for x in pd.to_numeric(d.week, errors="coerce").dropna().unique()),
    }


def rolling_mean(g: pd.DataFrame, base: str, window: int) -> Optional[float]:
    if base not in g.columns: return None
    x = pd.to_numeric(g.sort_values("week")[base], errors="coerce").dropna().tail(window)
    return float(x.mean()) if len(x) else None


def team_mean(team_hist: pd.DataFrame, team: str, base: str, window: int) -> Optional[float]:
    if team_hist.empty or base not in team_hist.columns: return None
    q = team_hist[team_hist.team.astype(str).eq(str(team))].sort_values("week")
    x = pd.to_numeric(q[base], errors="coerce").dropna().tail(window)
    return float(x.mean()) if len(x) else None


def latest_player_row(g: pd.DataFrame) -> dict:
    if g.empty: return {}
    return g.sort_values("week").iloc[-1].to_dict()


def build_competition_now(observed: pd.DataFrame) -> Dict[Tuple[str, str], Dict[str, float]]:
    if observed.empty: return {}
    last = observed.sort_values(["canonical_player_id", "week"]).groupby("canonical_player_id", as_index=False).tail(1).copy()
    # Upcoming prior shares should include the latest completed game, not the historical row's already-shifted prior4.
    shares = []
    for pid, g in observed.groupby("canonical_player_id"):
        row = latest_player_row(g); pos = str(row.get("position_model") or ""); team = str(row.get("team") or "")
        shares.append({"canonical_player_id": pid, "team": team, "position_model": pos,
                       "target": rolling_mean(g, "target_share", 4) or 0.0,
                       "carry": rolling_mean(g, "carry_share", 4) or 0.0,
                       "defsnap": rolling_mean(g, "defense_snap_share", 4) or 0.0})
    s = pd.DataFrame(shares); out = {}
    if s.empty: return out
    for r in s.itertuples(index=False):
        recv = s[(s.team == r.team) & s.position_model.isin(["WR", "TE", "RB"])]
        rb = s[(s.team == r.team) & s.position_model.eq("RB")]
        tk = s[(s.team == r.team) & s.position_model.isin(["LB", "S"])]
        pr = s[(s.team == r.team) & s.position_model.isin(["EDGE", "IDL"])]
        out[(str(r.canonical_player_id), str(r.position_model))] = {
            "receiving_competition_index": float(recv.target.sum() - r.target) if r.position_model in ["WR", "TE", "RB"] else math.nan,
            "backfield_competition_index": float(rb.carry.sum() - r.carry) if r.position_model == "RB" else math.nan,
            "tackle_competition_index": float(tk.defsnap.sum() - r.defsnap) if r.position_model in ["LB", "S"] else math.nan,
            "pass_rush_support_index": float(pr.defsnap.sum() - r.defsnap) if r.position_model in ["EDGE", "IDL"] else math.nan,
        }
    return out


def feature_value(feature: str, g: pd.DataFrame, team_hist: pd.DataFrame, team: str, opponent: Optional[str], competition: dict) -> Optional[float]:
    # Explicit special cases.
    if feature == "fp_prior_4": return rolling_mean(g, "fantasy_points", 4)
    if feature == "fp_prior_8": return rolling_mean(g, "fantasy_points", 8)
    if feature == "opportunity_change_score_prior1":
        x = pd.to_numeric(g.sort_values("week").get("opportunity_change_score"), errors="coerce").dropna() if "opportunity_change_score" in g else pd.Series(dtype=float)
        return float(x.iloc[-1]) if len(x) else None
    if feature in competition:
        x = competition.get(feature); return float(x) if x is not None and math.isfinite(float(x)) else None
    if feature.endswith("_prior4_team"):
        return team_mean(team_hist, team, feature[:-12], 4)
    if feature.endswith("_prior8_team"):
        return team_mean(team_hist, team, feature[:-12], 8)
    if feature.startswith("opponent_") and feature.endswith("_prior4"):
        return team_mean(team_hist, opponent or "", feature[len("opponent_"):-7], 4)
    if feature.startswith("opponent_") and feature.endswith("_prior8"):
        return team_mean(team_hist, opponent or "", feature[len("opponent_"):-7], 8)
    if feature.endswith("_prior4"):
        return rolling_mean(g, feature[:-7], 4)
    if feature.endswith("_prior8"):
        return rolling_mean(g, feature[:-7], 8)
    # Same-row fields permitted in historical M4 are themselves pregame constructs, e.g. competition indices.
    if feature in g.columns:
        x = pd.to_numeric(g.sort_values("week")[feature], errors="coerce").dropna()
        return float(x.iloc[-1]) if len(x) else None
    return None


def predict_linear_spec(spec: dict, values: Dict[str, Optional[float]]) -> Tuple[float, float]:
    fs = list(spec.get("features") or [])
    med = list(spec.get("imputer_medians") or [])
    mu = list(spec.get("scaler_mean") or [])
    sd = list(spec.get("scaler_scale") or [])
    co = list(spec.get("coefficients") or [])
    if not fs or not (len(fs) == len(med) == len(mu) == len(sd) == len(co)):
        raise ValueError("invalid exported Ridge spec")
    observed = 0; total = float(spec.get("intercept") or 0.0)
    for i, f in enumerate(fs):
        v = values.get(f)
        if v is None or not math.isfinite(float(v)):
            x = float(med[i])
        else:
            x = float(v); observed += 1
        scale = float(sd[i]) if float(sd[i]) else 1.0
        total += ((x - float(mu[i])) / scale) * float(co[i])
    floor = float(spec.get("prediction_floor") or 0.0)
    return max(floor, float(total)), observed / len(fs)


def predicted_stats_for_player(pos_spec: dict, values: dict) -> Tuple[dict, float]:
    stats = {}; cover = []
    for s in pos_spec.get("targets") or []:
        try:
            pred, cov = predict_linear_spec(s, values); stats[str(s.get("target"))] = pred; cover.append(cov)
        except Exception:
            continue
    return stats, float(np.mean(cover)) if cover else 0.0


def m5_risk_band(m5: dict, pos: str) -> Tuple[Optional[float], Optional[float]]:
    for r in m5.get("weekly_integration", {}).get("risk_bands", []) or []:
        if r.get("position") == pos:
            return (float(r["q10"]) if r.get("q10") is not None else None, float(r["q90"]) if r.get("q90") is not None else None)
    return None, None


def m4_blend_weight(m4: dict, pos: str) -> Optional[float]:
    for r in m4.get("blend", {}).get("aggregate", []) or []:
        if r.get("position") == pos and r.get("status") == "validated_candidate":
            w = r.get("recommended_fie_weight_next")
            return float(w) if w is not None else None
    return None


def m4_position_valid(m4: dict, pos: str) -> bool:
    return any(r.get("position") == pos and r.get("status") == "validated_candidate" for r in m4.get("final_position_models", {}).get("aggregate", []) or [])


def m5_gate(m5: dict, name: str, pos: str) -> bool:
    return pos in set(m5.get("activation", {}).get("decision_gates", {}).get(name, []) or [])


def sleeper_identity_maps(identity: pd.DataFrame, sp: dict) -> Tuple[Dict[str, str], Dict[str, dict]]:
    sid_to_cid = {}
    if not identity.empty and {"sleeper_id", "canonical_player_id"}.issubset(identity.columns):
        for r in identity.dropna(subset=["sleeper_id", "canonical_player_id"]).itertuples(index=False): sid_to_cid[str(r.sleeper_id)] = str(r.canonical_player_id)
    # Sleeper player endpoint often exposes gsis_id; use it as a second exact bridge.
    for sid, p in sp.items():
        gid = p.get("gsis_id") or p.get("player_id")
        if gid and str(gid).startswith("00-"):
            sid_to_cid.setdefault(str(sid), str(gid))
    return sid_to_cid, sp


def inferred_nfl_season(now_utc: Optional[datetime] = None) -> int:
    """Rollover-safe NFL season inference for unattended current builds.

    January/February belong to the season that began in the prior calendar year;
    from March onward the upcoming/current season uses the calendar year. Sleeper
    state and an explicit --season override remain higher-priority sources.
    """
    d = now_utc or datetime.now(timezone.utc)
    return d.year - 1 if d.month <= 2 else d.year


def build_snapshot(args) -> dict:
    m4 = load_json(args.m4_bundle); m5 = load_json(args.m5_bundle); m6 = load_json(args.m6_bundle)
    fallback_scoring = m5.get("scoring_settings") or DEFAULT_PPR
    scoring, scoring_prov = league_scoring(args.league_id, fallback_scoring)
    sig = scoring_signature(scoring)
    state = sleeper_state()
    season = int(args.season or state.get("season") or inferred_nfl_season())
    week = int(args.week or state.get("week") or 1)
    generated = utc_now(); cache = Path(args.cache_dir); schedule = load_schedule(cache)
    opponents = opponent_map(schedule, season, week)
    kickoff = first_kickoff_utc(schedule, season, week)
    pregame_eligible = bool(kickoff and datetime.now(timezone.utc) < kickoff)

    observed, team_hist, identity, source_meta = current_observed_frame(season, week, scoring, cache)
    sp = sleeper_players(); srows = sleeper_projection_rows(season, week)
    archive_meta = archive_sleeper_projection(srows, season, week, identity, Path(args.sleeper_archive), pregame_eligible)
    sid_to_cid, sp = sleeper_identity_maps(identity, sp)
    proj_by_sid = {}
    for r in srows:
        sid = str(r.get("player_id") or (r.get("player") or {}).get("player_id") or "")
        if sid: proj_by_sid[sid] = r

    m5_sig = m5.get("scoring_signature")
    research_compatible = bool(m5.get("status") == "complete" and m6.get("status") == "complete" and (not m5_sig or m5_sig == sig))
    specs = m4.get("final_position_models", {}).get("model_specs", {}).get("positions", {}) or {}
    comp = build_competition_now(observed)
    players = []
    observed_groups = {str(pid): g.copy() for pid, g in observed.groupby("canonical_player_id")} if not observed.empty else {}

    # Universe is Sleeper projections plus current observed players, keeping records identifiable to the browser.
    universe = set(proj_by_sid)
    if not observed.empty:
        rev = {}
        if not identity.empty and {"canonical_player_id", "sleeper_id"}.issubset(identity.columns):
            rev = {str(r.canonical_player_id): str(r.sleeper_id) for r in identity.dropna(subset=["canonical_player_id", "sleeper_id"]).itertuples(index=False)}
        for cid in observed.canonical_player_id.astype(str).unique():
            if cid in rev: universe.add(rev[cid])

    for sid in sorted(universe):
        pp = sp.get(sid) or {}; sr = proj_by_sid.get(sid) or {}; raw_stats = sr.get("stats") or sr or {}
        cid = sid_to_cid.get(sid)
        pos = normalize_position(pp.get("position") or (sr.get("player") or {}).get("position") or "")
        name = pp.get("full_name") or pp.get("first_name", "") + (" " if pp.get("first_name") and pp.get("last_name") else "") + pp.get("last_name", "")
        team = str(pp.get("team") or "")
        g = observed_groups.get(str(cid), pd.DataFrame()) if cid else pd.DataFrame()
        if not g.empty:
            lr = latest_player_row(g); team = str(lr.get("team") or team); pos = str(lr.get("position_model") or pos); name = str(lr.get("full_name") or name)
        opponent = opponents.get(team)
        sleeper_fp = score_sleeper_projection(raw_stats, scoring, pos) if raw_stats else None
        history_games = int(len(g)) if not g.empty else 0
        feature_values = {}; fie_stats = {}; feature_coverage = 0.0; fie_fp = None
        psp = specs.get(pos) if isinstance(specs, dict) else None
        if psp and not g.empty:
            cvals = comp.get((str(cid), pos), {})
            for f in psp.get("features") or []:
                feature_values[f] = feature_value(f, g, team_hist, team, opponent, cvals)
            fie_stats, feature_coverage = predicted_stats_for_player(psp, feature_values)
            if fie_stats:
                frame = pd.DataFrame([{**fie_stats, "position_model": pos}])
                fie_fp = float(score_rows(frame, scoring).iloc[0])
        weekly_model_ok = research_compatible and m4_position_valid(m4, pos) and m5_gate(m5, "weekly_mean_positions", pos)
        activation_eligible = bool(weekly_model_ok and history_games >= 2 and feature_coverage >= args.min_feature_coverage and fie_fp is not None and math.isfinite(float(fie_fp)))
        blend_w = m4_blend_weight(m4, pos)
        if activation_eligible and blend_w is not None and sleeper_fp is not None and math.isfinite(float(sleeper_fp)):
            decision = blend_w * fie_fp + (1.0 - blend_w) * float(sleeper_fp); source = f"M6 blend FIE {blend_w:.2f} / Sleeper {1-blend_w:.2f}"
        elif activation_eligible:
            decision = fie_fp; source = "M6 FIE raw-stat model"
        elif sleeper_fp is not None:
            decision = float(sleeper_fp); source = "Sleeper diagnostic only (M6 gate off)"
        else:
            decision = None; source = "Unavailable"
        q10, q90 = m5_risk_band(m5, pos)
        risk_ok = activation_eligible and m5_gate(m5, "weekly_risk_positions", pos)
        p10 = max(0.0, decision + q10) if decision is not None and risk_ok and q10 is not None else None
        p90 = max(decision, decision + q90) if decision is not None and risk_ok and q90 is not None else None

        # Waiver next-3 spec is allowed to use the just-completed role signal. Missing xFP fields are imputed by the exported model, but coverage is surfaced.
        waiver_next3 = None
        wspec = m5.get("waiver_integration", {}).get("model_specs", {}).get("positions", {}).get(pos)
        if activation_eligible and m5_gate(m5, "waiver_policy_positions", pos) and wspec and not g.empty:
            latest = latest_player_row(g); wvals = {"fie_projection": decision, "fp_prior_4": rolling_mean(g, "fantasy_points", 4)}
            for f in wspec.get("features") or []:
                if f in wvals: continue
                v = latest.get(f)
                try: wvals[f] = float(v) if v is not None and math.isfinite(float(v)) else None
                except Exception: wvals[f] = None
            try: waiver_next3, _ = predict_linear_spec(wspec, wvals)
            except Exception: waiver_next3 = None

        confidence = int(round(max(5, min(95, 35 + feature_coverage * 60)))) if activation_eligible else int(round(max(5, min(60, 10 + feature_coverage * 40))))
        players.append({
            "sleeper_id": sid, "canonical_player_id": cid, "full_name": name.strip() or None,
            "team": team or None, "opponent": opponent, "position_model": pos,
            "season": season, "week": week, "history_games": history_games,
            "activation_eligible": activation_eligible, "projection_source": source,
            "decision_weekly_projection": round(float(decision), 4) if decision is not None and math.isfinite(float(decision)) else None,
            "fie_weekly_projection": round(float(fie_fp), 4) if fie_fp is not None and math.isfinite(float(fie_fp)) else None,
            "sleeper_weekly_projection": round(float(sleeper_fp), 4) if sleeper_fp is not None and math.isfinite(float(sleeper_fp)) else None,
            "p10": round(float(p10), 4) if p10 is not None else None,
            "p90": round(float(p90), 4) if p90 is not None else None,
            "waiver_next3_projection": round(float(waiver_next3), 4) if waiver_next3 is not None else None,
            "young_role_probability": None, "spike_probability": None, "bust_probability": None,
            "confidence": confidence, "feature_coverage": round(float(feature_coverage), 4),
            "predicted_stats": {k: round(float(v), 4) for k, v in fie_stats.items()} if fie_stats else {},
        })

    eligible = sum(1 for r in players if r["activation_eligible"])
    status = "complete" if players else "ready"
    bundle = {
        "schema_version": 2, "m5_build": M5_BUILD, "producer_build": PRODUCER_BUILD,
        "generated_at": generated, "status": status, "season": season, "week": week,
        "scoring_signature": sig, "scoring_settings": scoring, "scoring_provenance": scoring_prov,
        "research_compatible": research_compatible, "snapshot_max_age_hours": 18,
        "target_week_realised_stats_excluded": True,
        "players": players,
        "summary": {"players": len(players), "activation_eligible": eligible, "fie_projected": sum(r["fie_weekly_projection"] is not None for r in players), "sleeper_projected": sum(r["sleeper_weekly_projection"] is not None for r in players)},
        "source_health": source_meta, "sleeper_archive": archive_meta,
        "kickoff": {"first_kickoff_utc": kickoff.isoformat() if kickoff else None, "capture_pregame_eligible": pregame_eligible},
        "guardrails": [
            "No target-week realised stats are used in target-week FIE features.",
            "At least two completed prior games and minimum feature coverage are required for FIE activation.",
            "M4 weekly model and M5 weekly decision gate must both validate the position.",
            "Scoring signature must match the empirical M5 research profile.",
        ],
    }
    return bundle


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build FIE V8.8-M6 current-season decision snapshot")
    p.add_argument("--league-id", default=None)
    p.add_argument("--season", type=int, default=None)
    p.add_argument("--week", type=int, default=None)
    p.add_argument("--m4-bundle", default="data/research/milestone4.json")
    p.add_argument("--m5-bundle", default="data/research/milestone5.json")
    p.add_argument("--m6-bundle", default="data/research/milestone6.json")
    p.add_argument("--cache-dir", default=".cache/fie-current")
    p.add_argument("--sleeper-archive", default="data/research/market/sleeper")
    p.add_argument("--output", default="data/research/current/milestone5_current.json")
    p.add_argument("--min-feature-coverage", type=float, default=.45)
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv); b = build_snapshot(a)
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(b, indent=2, allow_nan=False))
    print(f"Wrote {out} status={b['status']} season={b['season']} week={b['week']} eligible={b['summary']['activation_eligible']}/{b['summary']['players']}")


if __name__ == "__main__":
    main()
