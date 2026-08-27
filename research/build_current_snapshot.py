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
import hashlib
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
from league_profile import sha256_json, structural_contract
from scoring_relevance import relevant_scoring_audit, position_support
from dst_contract import dst_enabled, dst_profile_fields
from fie_dst import predict_dst_from_bundle, score_dst_stats
from kicker_contract import kicker_profile_fields
from fie_kicker import predict_from_bundle as predict_kicker_from_bundle, score_kicker_stats

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
    return scoring, {
        "type": "sleeper_league", "league_id": str(league_id), "league_name": league.get("name"),
        "profile_fields": {"roster_positions": league.get("roster_positions") or [], "settings": league.get("settings") or {},
          "total_rosters": league.get("total_rosters"), "season": league.get("season"), "season_type": league.get("season_type")},
    }


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


def regular_schedule_slice(schedule: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """Return only regular-season games for a numbered NFL week.

    nflverse contains preseason and postseason games in the same schedule table.
    A bare season/week filter can therefore bind Sleeper preseason Week 3 to NFL
    regular-season Week 3, which is precisely what a pregame benchmark must not do.
    """
    if schedule.empty or not {"season", "week"}.issubset(schedule.columns):
        return pd.DataFrame()
    s = schedule[(pd.to_numeric(schedule["season"], errors="coerce") == season) & (pd.to_numeric(schedule["week"], errors="coerce") == week)].copy()
    gt = next((c for c in ["game_type", "season_type", "type"] if c in s.columns), None)
    if gt:
        vals = s[gt].astype(str).str.upper().str.replace("_", "", regex=False)
        s = s[vals.isin(["REG", "REGULAR", "REGULARSEASON"])].copy()
    return s


def normalize_season_type(value) -> str:
    v = str(value or "").strip().lower().replace("_", "")
    if v in {"regular", "reg", "regularseason"}: return "regular"
    if v in {"pre", "preseason"}: return "preseason"
    if v in {"post", "postseason", "playoffs"}: return "postseason"
    return v or "unknown"


def resolve_analysis_week(explicit_week: Optional[int], sleeper_week: int, season_type: str) -> int:
    if explicit_week is not None:
        return int(explicit_week)
    return 1 if normalize_season_type(season_type) == "preseason" else int(sleeper_week or 1)


def opponent_map(schedule: pd.DataFrame, season: int, week: int) -> Dict[str, str]:
    s = regular_schedule_slice(schedule, season, week)
    hc = next((c for c in ["home_team", "home"] if c in s.columns), None)
    ac = next((c for c in ["away_team", "away"] if c in s.columns), None)
    if not hc or not ac: return {}
    out = {}
    for r in s.itertuples(index=False):
        h = str(getattr(r, hc) or ""); a = str(getattr(r, ac) or "")
        if h and a: out[h] = a; out[a] = h
    return out


def dst_game_context_map(schedule: pd.DataFrame, season: int, week: int) -> Dict[str, dict]:
    s = regular_schedule_slice(schedule, season, week)
    if s.empty: return {}
    hc = next((c for c in ["home_team", "home"] if c in s.columns), None)
    ac = next((c for c in ["away_team", "away"] if c in s.columns), None)
    if not hc or not ac: return {}
    out = {}
    for _, r in s.iterrows():
        h, a = str(r.get(hc) or ""), str(r.get(ac) or "")
        total = pd.to_numeric(pd.Series([r.get("total_line")]), errors="coerce").iloc[0] if "total_line" in s.columns else np.nan
        spread = pd.to_numeric(pd.Series([r.get("spread_line")]), errors="coerce").iloc[0] if "spread_line" in s.columns else np.nan
        if h:
            out[h] = {"opponent": a or None, "home": 1.0, "spread_line": float(spread) if pd.notna(spread) else None, "total_line": float(total) if pd.notna(total) else None}
        if a:
            out[a] = {"opponent": h or None, "home": 0.0, "spread_line": (-float(spread)) if pd.notna(spread) else None, "total_line": float(total) if pd.notna(total) else None}
    return out


def first_kickoff_utc(schedule: pd.DataFrame, season: int, week: int) -> Optional[datetime]:
    s = regular_schedule_slice(schedule, season, week)
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


def market_capture_decision(season_type: str, kickoff: Optional[datetime], *, now: Optional[datetime] = None, window_hours: float = 18.0) -> dict:
    """Single timing policy for every immutable Sleeper benchmark capture path."""
    now = now or datetime.now(timezone.utc)
    st = normalize_season_type(season_type)
    base = {
        "capture_policy_version": 2,
        "season_type": st,
        "capture_window_hours": float(window_hours),
        "first_kickoff_utc": kickoff.isoformat() if kickoff else None,
        "hours_before_kickoff": None,
        "pregame_eligible": False,
    }
    if st != "regular":
        return {**base, "reason": f"season_type_{st}"}
    if kickoff is None:
        return {**base, "reason": "kickoff_unverified"}
    hours = (kickoff - now).total_seconds() / 3600.0
    base["hours_before_kickoff"] = round(float(hours), 6)
    if hours <= 0:
        return {**base, "reason": "kickoff_already_started"}
    if hours > float(window_hours):
        return {**base, "reason": "before_capture_window"}
    return {**base, "pregame_eligible": True, "reason": "timing_verified"}


def sleeper_players() -> dict:
    rows = get_json("https://api.sleeper.app/v1/players/nfl", required=False) or {}
    return rows if isinstance(rows, dict) else {}


def sleeper_projection_rows(season: int, week: int) -> List[dict]:
    rows = get_json(f"https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular", required=False) or []
    return rows if isinstance(rows, list) else []


def score_sleeper_projection(stats: dict, scoring: dict, position: str = "") -> float:
    st = stats or {}
    if str(position or "").upper() == "K":
        z = score_kicker_stats(st, scoring)
        if z.get("exact") and z.get("supported_keys"):
            return float(z.get("points") or 0.0)
        for k in ["pts_ppr", "pts_half_ppr", "pts_std", "pts"]:
            try:
                v = float(st.get(k))
                if math.isfinite(v): return v
            except (TypeError, ValueError): pass
    if str(position or "").upper() in {"DEF", "DST"}:
        z = score_dst_stats(st, scoring)
        if z.get("exact") and z.get("supported_keys"):
            return float(z.get("points") or 0.0)
        # Sleeper sometimes publishes an already-scored baseline even when raw
        # nonlinear bucket inputs are omitted. Prefer that to inventing points.
        for k in ["pts_ppr", "pts_half_ppr", "pts_std", "pts"]:
            try:
                v = float(st.get(k))
                if math.isfinite(v): return v
            except (TypeError, ValueError): pass
    total = 0.0
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


def archive_sleeper_projection(rows: List[dict], season: int, week: int, identity: pd.DataFrame, output_root: Path, pregame_eligible: bool, capture_context: Optional[dict] = None) -> dict:
    out = output_root / str(season) / f"week_{week:02d}.jsonl.gz"
    manifest_path = output_root / "manifest.json"

    def sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def read_existing_meta(path: Path) -> dict:
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        if meta_path.exists():
            try:
                return json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        # Legacy first-write snapshots may predate sidecar metadata.  Recover
        # immutable facts from the stored rows without changing the snapshot.
        first = None; n = 0
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip(): continue
                    r = json.loads(line); n += 1
                    if first is None: first = r
        except Exception:
            first = None
        return {
            "season": season, "week": week,
            "captured_at": (first or {}).get("captured_at"),
            "pregame_eligible": bool((first or {}).get("pregame_eligible", False)),
            "rows": n, "first_write_policy": True, "source": "Sleeper projection endpoint",
        }

    def register(path: Path, meta: dict, *, written: bool) -> dict:
        digest = sha256_file(path)
        meta = {**meta, "sha256": digest, "path": str(path)}
        sidecar = path.with_suffix(path.suffix + ".meta.json")
        if not sidecar.exists():
            sidecar.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest = {"schema_version": 1, "snapshots": {}}
        if manifest_path.exists():
            try: manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception: pass
        manifest.setdefault("schema_version", 1); manifest.setdefault("snapshots", {})
        key = f"{season}-W{week:02d}"
        existing = manifest["snapshots"].get(key)
        if existing and existing.get("sha256") and existing.get("sha256") != digest:
            raise RuntimeError(f"Immutable Sleeper archive hash changed for {key}")
        manifest["snapshots"][key] = {
            "season": season, "week": week, "path": str(path), "sha256": digest,
            "captured_at": meta.get("captured_at"), "pregame_eligible": bool(meta.get("pregame_eligible")),
            "rows": int(meta.get("rows") or 0),
            "capture_policy_version": meta.get("capture_policy_version"),
            "season_type": meta.get("season_type"),
            "first_kickoff_utc": meta.get("first_kickoff_utc"),
            "hours_before_kickoff": meta.get("hours_before_kickoff"),
            "capture_window_hours": meta.get("capture_window_hours"),
        }
        manifest["updated_at"] = utc_now()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {**meta, "written": written, "first_write": True, "manifest": str(manifest_path)}

    if out.exists():
        return register(out, read_existing_meta(out), written=False)
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
                   "capture_policy_version": (capture_context or {}).get("capture_policy_version"),
                   "season_type": (capture_context or {}).get("season_type"),
                   "sleeper_id": sid, "canonical_player_id": imap.get(sid),
                   "position_model": normalize_position((r.get("player") or {}).get("position")), "stats": r.get("stats") or r}
            h.write(json.dumps(rec, separators=(",", ":")) + "\n"); n += 1
    meta = {
        "season": season, "week": week, "captured_at": captured,
        "pregame_eligible": bool(pregame_eligible), "rows": n,
        "first_write_policy": True, "source": "Sleeper projection endpoint",
        **(capture_context or {}),
    }
    return register(out, meta, written=True)


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


def _finite_or_none(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def current_player_features(g: pd.DataFrame, team_hist: pd.DataFrame, team: str, opponent: Optional[str], competition: dict) -> dict:
    """Export leakage-safe current opportunity/context features for the browser.

    All values are calculated only from completed weeks already admitted to
    ``observed``.  The live client may display these diagnostically regardless
    of M6 activation, but only governance-eligible models may use them to alter
    decisions.  Pass-play participation remains explicitly a proxy and is not
    relabelled as a true route participation rate.
    """
    if g.empty:
        return {}
    metrics = [
        "snap_share", "offense_snap_share", "defense_snap_share",
        "target_share", "carry_share", "qb_rush_share",
        "red_zone_target_share", "red_zone_carry_share",
        "inside_10_carry_share", "inside_5_carry_share",
        "pass_play_participation_proxy", "end_zone_target_share_proxy",
        "opportunity_change_score",
    ]
    out = {}
    for metric in metrics:
        v = rolling_mean(g, metric, 4)
        if v is not None and math.isfinite(float(v)):
            out[metric] = round(float(v), 6)
    for k, v in (competition or {}).items():
        fv = _finite_or_none(v)
        if fv is not None:
            out[k] = round(fv, 6)
    for metric in ["team_plays", "team_pass_attempts", "team_rush_attempts", "team_red_zone_plays", "team_goal_line_plays"]:
        v = team_mean(team_hist, team, metric, 4)
        if v is not None and math.isfinite(float(v)):
            out[f"{metric}_prior4"] = round(float(v), 6)
    if opponent:
        for metric in ["team_plays", "team_pass_attempts", "team_rush_attempts"]:
            v = team_mean(team_hist, opponent, metric, 4)
            if v is not None and math.isfinite(float(v)):
                out[f"opponent_{metric}_prior4"] = round(float(v), 6)
    last_week = pd.to_numeric(g.get("week"), errors="coerce").dropna() if "week" in g else pd.Series(dtype=float)
    return {
        "schema_version": 1,
        "as_of_completed_week": int(last_week.max()) if len(last_week) else None,
        "window_games": min(4, int(len(g))),
        "source": "nflverse completed-week derived opportunity/context",
        "leakage_safe": True,
        "route_participation_is_proxy": "pass_play_participation_proxy" in out,
        "values": out,
    }


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


def m5_format_gate(m5: dict, decision: str, league_format: str | None, pos: str) -> bool:
    """Apply the decision-specific format gate when the League-ID profile is known.

    Legacy/global snapshots without a profile retain the older generic decision
    gate for backwards compatibility. Namespaced production snapshots must agree
    with the browser's stricter decision+format contract.
    """
    generic_name = {"weekly": "weekly_mean_positions", "draft": "draft_policy_positions", "waiver": "waiver_policy_positions"}.get(decision)
    if not generic_name or not m5_gate(m5, generic_name, pos):
        return False
    fmt = str(league_format or "").upper().strip()
    by_decision = m5.get("activation", {}).get("decision_gates", {}).get("decision_format_position_gates", {}) or {}
    by_format = by_decision.get(decision, {}) if isinstance(by_decision, dict) else {}
    if not fmt or not isinstance(by_format, dict) or fmt not in by_format:
        return True
    return pos in set(by_format.get(fmt, []) or [])


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
    profile = load_json(getattr(args, "league_profile", None)) if getattr(args, "league_profile", None) else {}
    profile_league_id = str(profile.get("league_id") or "")
    league_id = str(args.league_id or profile_league_id or "") or None
    if profile and not league_id:
        raise RuntimeError("league profile is present but no League ID could be resolved")
    if profile_league_id and league_id and profile_league_id != league_id:
        raise RuntimeError(f"league profile belongs to {profile_league_id}, not {league_id}")
    fallback_scoring = m5.get("scoring_settings") or profile.get("scoring_settings") or DEFAULT_PPR
    scoring, scoring_prov = league_scoring(league_id, fallback_scoring)
    sig = scoring_signature(scoring)
    profile_sig = profile.get("scoring_signature")
    profile_fp = profile.get("profile_fingerprint")
    league_format = str(profile.get("format") or "").upper() or None
    live_profile_fp = None
    profile_current_match = True
    profile_diff = {}
    if profile and league_id:
        pf = scoring_prov.get("profile_fields") or {}
        live_contract = structural_contract(
            str(league_id), str(profile.get("format") or "AUTO"), scoring,
            pf.get("roster_positions") or [], pf.get("settings") or {},
            pf.get("total_rosters"), pf.get("season"), pf.get("season_type"),
            profile.get("research_constraints") or None,
        )
        live_profile_fp = sha256_json(live_contract)
        profile_current_match = bool(profile_fp and live_profile_fp == profile_fp)
        stored_contract = structural_contract(
            str(league_id), str(profile.get("format") or "AUTO"), profile.get("scoring_settings") or {},
            profile.get("roster_positions") or [], profile.get("settings") or {},
            profile.get("total_rosters"), profile.get("season"), profile.get("season_type"),
            profile.get("research_constraints") or None,
        )
        profile_diff = {k: {"stored": stored_contract.get(k), "live": live_contract.get(k)}
                        for k in sorted(set(stored_contract) | set(live_contract))
                        if stored_contract.get(k) != live_contract.get(k)}
    artifact_identity_ok = True
    if profile:
        for label, bundle in (("M4",m4),("M5",m5),("M6",m6)):
            bid=str(bundle.get("league_id") or "")
            bfp=bundle.get("profile_fingerprint")
            if bid != league_id or bfp != profile_fp:
                artifact_identity_ok=False
                break
    state = sleeper_state()
    season = int(args.season or state.get("season") or inferred_nfl_season())
    sleeper_week = int(state.get("week") or 1)
    season_type = normalize_season_type(state.get("season_type"))
    # Sleeper's preseason week counter is not the regular-season decision week.
    # Unless the operator explicitly supplies --week, preseason analysis points at
    # upcoming regular-season Week 1 while retaining the source-state metadata.
    week = resolve_analysis_week(args.week, sleeper_week, season_type)
    generated = utc_now(); cache = Path(args.cache_dir); schedule = load_schedule(cache)
    opponents = opponent_map(schedule, season, week)
    dst_contexts = dst_game_context_map(schedule, season, week)
    dst_meta = dst_profile_fields(profile) if profile else {"dst_enabled": False, "dst_starter_slots": 0, "dst_scoring_settings": {}, "dst_scoring_signature": None, "dst_roster_signature": None}
    kicker_meta = kicker_profile_fields(profile) if profile else {"kicker_enabled": False, "kicker_starter_slots": 0, "kicker_scoring_settings": {}, "kicker_scoring_signature": None, "kicker_roster_signature": None}
    kickoff = first_kickoff_utc(schedule, season, week)
    capture_decision = market_capture_decision(season_type, kickoff, window_hours=18.0)
    pregame_eligible = bool(capture_decision.get("pregame_eligible"))

    observed, team_hist, identity, source_meta = current_observed_frame(season, week, scoring, cache)
    scoring_support_raw = source_meta.get("scoring_support") or {}
    scoring_support_relevant = relevant_scoring_audit(scoring, scoring_support_raw, profile.get("roster_positions") or []) if profile else scoring_support_raw
    sp = sleeper_players(); srows = sleeper_projection_rows(season, week)
    if pregame_eligible:
        archive_meta = archive_sleeper_projection(
            srows, season, week, identity, Path(args.sleeper_archive), True, capture_context=capture_decision
        )
    else:
        archive_meta = {
            "written": False, "skipped": True, "season": season, "week": week,
            "pregame_eligible": False, **capture_decision,
        }
    sid_to_cid, sp = sleeper_identity_maps(identity, sp)
    proj_by_sid = {}
    for r in srows:
        sid = str(r.get("player_id") or (r.get("player") or {}).get("player_id") or "")
        if sid: proj_by_sid[sid] = r

    m5_sig = m5.get("scoring_signature")
    research_compatible = bool(
        m5.get("status") == "complete" and m6.get("status") == "complete"
        and (not m5_sig or m5_sig == sig)
        and (not profile_sig or profile_sig == sig)
        and artifact_identity_ok
        and profile_current_match
    )
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
        if pos == "DEF" and not dst_meta.get("dst_enabled"):
            continue
        if pos == "K" and not kicker_meta.get("kicker_enabled"):
            continue
        sleeper_fp = score_sleeper_projection(raw_stats, scoring, pos) if raw_stats else None
        # D/ST has a dedicated team-week path. It intentionally does not require two
        # current-season player games, so a validated prior can operate in Week 1.
        if pos == "DEF":
            dmodel = m4.get("dst") or {}
            ctx = dst_contexts.get(team, {})
            opponent = ctx.get("opponent") or opponent
            dp = predict_dst_from_bundle(dmodel, team, opponent, home=ctx.get("home"), spread_line=ctx.get("spread_line"), total_line=ctx.get("total_line")) if dmodel else {"predicted_stats": {}, "feature_coverage": 0.0, "features": {}}
            fie_stats = dp.get("predicted_stats") or {}
            feature_coverage = float(dp.get("feature_coverage") or 0.0)
            scored = score_dst_stats(fie_stats, scoring) if fie_stats else {"points": None, "exact": False}
            fie_fp = scored.get("points") if scored.get("exact") and fie_stats else None
            weekly_model_ok = bool(research_compatible and dmodel.get("status") == "validated_candidate" and m5_format_gate(m5, "weekly", league_format, "DEF"))
            weekly_activation_eligible = bool(weekly_model_ok and feature_coverage >= args.min_feature_coverage and fie_fp is not None and math.isfinite(float(fie_fp)))
            decision = float(fie_fp) if weekly_activation_eligible else (float(sleeper_fp) if sleeper_fp is not None and math.isfinite(float(sleeper_fp)) else None)
            source = "M6 FIE D/ST raw-outcome model" if weekly_activation_eligible else ("Sleeper D/ST baseline (FIE gate off)" if sleeper_fp is not None else "Unavailable")
            q10, q90 = m5_risk_band(m5, "DEF")
            risk_ok = weekly_activation_eligible and m5_gate(m5, "weekly_risk_positions", "DEF")
            p10 = decision + q10 if decision is not None and risk_ok and q10 is not None else None
            p90 = decision + q90 if decision is not None and risk_ok and q90 is not None else None
            # A validated next-3 D/ST model uses the same pregame prior with future
            # opponents. Exact future market lines are intentionally not fabricated.
            next3_vals = []
            if dmodel.get("status") == "validated_candidate":
                for w in range(week, min(19, week + 3)):
                    cm = dst_game_context_map(schedule, season, w).get(team, {})
                    opp = cm.get("opponent")
                    if not opp: continue
                    ppred = predict_dst_from_bundle(dmodel, team, opp, home=cm.get("home"), spread_line=cm.get("spread_line"), total_line=cm.get("total_line"))
                    ss = score_dst_stats(ppred.get("predicted_stats") or {}, scoring)
                    if ss.get("exact"): next3_vals.append(float(ss["points"]))
            waiver_next3 = float(np.mean(next3_vals)) if next3_vals else None
            waiver_activation_eligible = bool(weekly_activation_eligible and m5_format_gate(m5, "waiver", league_format, "DEF") and waiver_next3 is not None)
            confidence = int(round(max(5, min(95, 35 + feature_coverage * 60)))) if weekly_activation_eligible else 35
            players.append({
                "sleeper_id": sid, "canonical_player_id": f"DST:{team or sid}", "entity_type": "TEAM_DEFENSE", "full_name": f"{team or sid} D/ST",
                "team": team or sid, "opponent": opponent, "position_model": "DEF", "season": season, "week": week, "history_games": 0,
                "activation_eligible": weekly_activation_eligible, "weekly_activation_eligible": weekly_activation_eligible, "waiver_activation_eligible": waiver_activation_eligible,
                "projection_source": source, "decision_weekly_projection": round(float(decision),4) if decision is not None else None,
                "fie_weekly_projection": round(float(fie_fp),4) if fie_fp is not None else None, "sleeper_weekly_projection": round(float(sleeper_fp),4) if sleeper_fp is not None else None,
                "p10": round(float(p10),4) if p10 is not None else None, "p90": round(float(p90),4) if p90 is not None else None,
                "waiver_next3_projection": round(float(waiver_next3),4) if waiver_activation_eligible else None, "waiver_feature_coverage": round(float(feature_coverage),4),
                "young_role_probability": None, "spike_probability": None, "bust_probability": None, "confidence": confidence, "feature_coverage": round(float(feature_coverage),4),
                "current_features": {"values": dp.get("features") or {}, "entity_type": "TEAM_DEFENSE"},
                "predicted_stats": {k: round(float(v),4) for k,v in fie_stats.items()},
                "dst_context": {"home": ctx.get("home"), "spread_line": ctx.get("spread_line"), "total_line": ctx.get("total_line"), "opponent_implied_points": (((float(ctx["total_line"]) - float(ctx.get("spread_line") or 0.0)) / 2.0) if ctx.get("total_line") is not None else None), "scoring_signature": dst_meta.get("dst_scoring_signature")},
            })
            continue
        # Kicker Intelligence mirrors D/ST's specialist path: a team opportunity/
        # distance/conversion model is scored only after raw outcomes are projected.
        # This permits exact per-yard and distance-specific miss scoring.
        if pos == "K":
            kmodel = m4.get("kicker") or {}
            ctx = dst_contexts.get(team, {})
            opponent = ctx.get("opponent") or opponent
            kp = predict_kicker_from_bundle(kmodel, team, home=ctx.get("home"), spread_line=ctx.get("spread_line"), total_line=ctx.get("total_line")) if kmodel else {"predicted_stats": {}, "feature_coverage": 0.0, "features": {}}
            fie_stats = kp.get("predicted_stats") or {}
            feature_coverage = float(kp.get("feature_coverage") or 0.0)
            scored = score_kicker_stats(fie_stats, scoring) if fie_stats else {"points": None, "exact": False}
            fie_fp = scored.get("points") if scored.get("exact") and fie_stats else None
            weekly_model_ok = bool(research_compatible and kmodel.get("status") == "validated_candidate" and m5_format_gate(m5, "weekly", league_format, "K"))
            weekly_activation_eligible = bool(weekly_model_ok and feature_coverage >= args.min_feature_coverage and fie_fp is not None and math.isfinite(float(fie_fp)))
            decision = float(fie_fp) if weekly_activation_eligible else (float(sleeper_fp) if sleeper_fp is not None and math.isfinite(float(sleeper_fp)) else None)
            source = "M6 FIE K raw-outcome model" if weekly_activation_eligible else ("Sleeper K baseline (FIE gate off)" if sleeper_fp is not None else "Unavailable")
            q10, q90 = m5_risk_band(m5, "K"); risk_ok = weekly_activation_eligible and m5_gate(m5, "weekly_risk_positions", "K")
            p10 = decision + q10 if decision is not None and risk_ok and q10 is not None else None
            p90 = decision + q90 if decision is not None and risk_ok and q90 is not None else None
            next3_vals = []
            if kmodel.get("status") == "validated_candidate":
                for w in range(week, min(19, week + 3)):
                    cm = dst_game_context_map(schedule, season, w).get(team, {})
                    if not cm.get("opponent"): continue
                    ppred = predict_kicker_from_bundle(kmodel, team, home=cm.get("home"), spread_line=cm.get("spread_line"), total_line=cm.get("total_line"))
                    ss = score_kicker_stats(ppred.get("predicted_stats") or {}, scoring)
                    if ss.get("exact"): next3_vals.append(float(ss["points"]))
            waiver_next3 = float(np.mean(next3_vals)) if next3_vals else None
            waiver_activation_eligible = bool(weekly_activation_eligible and m5_format_gate(m5, "waiver", league_format, "K") and waiver_next3 is not None)
            confidence = int(round(max(5, min(95, 35 + feature_coverage * 60)))) if weekly_activation_eligible else 35
            team_implied = (((float(ctx["total_line"]) + float(ctx.get("spread_line") or 0.0)) / 2.0) if ctx.get("total_line") is not None else None)
            players.append({
                "sleeper_id": sid, "canonical_player_id": cid or f"K:{sid}", "entity_type": "KICKER", "full_name": name.strip() or None,
                "team": team or None, "opponent": opponent, "position_model": "K", "season": season, "week": week, "history_games": int(len(g)) if not g.empty else 0,
                "activation_eligible": weekly_activation_eligible, "weekly_activation_eligible": weekly_activation_eligible, "waiver_activation_eligible": waiver_activation_eligible,
                "projection_source": source, "decision_weekly_projection": round(float(decision),4) if decision is not None else None,
                "fie_weekly_projection": round(float(fie_fp),4) if fie_fp is not None else None, "sleeper_weekly_projection": round(float(sleeper_fp),4) if sleeper_fp is not None else None,
                "p10": round(float(p10),4) if p10 is not None else None, "p90": round(float(p90),4) if p90 is not None else None,
                "waiver_next3_projection": round(float(waiver_next3),4) if waiver_activation_eligible else None, "waiver_feature_coverage": round(float(feature_coverage),4),
                "young_role_probability": None, "spike_probability": None, "bust_probability": None, "confidence": confidence, "feature_coverage": round(float(feature_coverage),4),
                "current_features": {"values": kp.get("features") or {}, "entity_type": "KICKER"}, "predicted_stats": {k: round(float(v),4) for k,v in fie_stats.items()},
                "kicker_context": {"home": ctx.get("home"), "spread_line": ctx.get("spread_line"), "total_line": ctx.get("total_line"), "team_implied_points": team_implied, "scoring_signature": kicker_meta.get("kicker_scoring_signature")},
            })
            continue
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
        pos_scoring = position_support(scoring, scoring_support_raw, pos)
        weekly_model_ok = research_compatible and pos_scoring.get("exact", False) and m4_position_valid(m4, pos) and m5_format_gate(m5, "weekly", league_format, pos)
        weekly_activation_eligible = bool(weekly_model_ok and history_games >= 2 and feature_coverage >= args.min_feature_coverage and fie_fp is not None and math.isfinite(float(fie_fp)))
        blend_w = m4_blend_weight(m4, pos)
        if weekly_activation_eligible and blend_w is not None and sleeper_fp is not None and math.isfinite(float(sleeper_fp)):
            decision = blend_w * fie_fp + (1.0 - blend_w) * float(sleeper_fp); source = f"M6 blend FIE {blend_w:.2f} / Sleeper {1-blend_w:.2f}"
        elif weekly_activation_eligible:
            decision = fie_fp; source = "M6 FIE raw-stat model"
        elif sleeper_fp is not None:
            decision = float(sleeper_fp); source = "Sleeper diagnostic only (M6 gate off)"
        else:
            decision = None; source = "Unavailable"
        q10, q90 = m5_risk_band(m5, pos)
        risk_ok = weekly_activation_eligible and m5_gate(m5, "weekly_risk_positions", pos)
        p10 = max(0.0, decision + q10) if decision is not None and risk_ok and q10 is not None else None
        p90 = max(decision, decision + q90) if decision is not None and risk_ok and q90 is not None else None

        # Waiver is a separate decision model.  It is allowed to activate even
        # when the same-position M4 weekly model remains diagnostic, provided
        # its own M5 next-3 gate and live feature-coverage checks pass.
        waiver_next3 = None
        waiver_feature_coverage = 0.0
        waiver_activation_eligible = False
        wspec = m5.get("waiver_integration", {}).get("model_specs", {}).get("positions", {}).get(pos)
        if research_compatible and pos_scoring.get("exact", False) and m5_format_gate(m5, "waiver", league_format, pos) and wspec and not g.empty and history_games >= 2:
            cvals = comp.get((str(cid), pos), {})
            wvals = {f: feature_value(f, g, team_hist, team, opponent, cvals) for f in (wspec.get("features") or [])}
            try:
                waiver_next3, waiver_feature_coverage = predict_linear_spec(wspec, wvals)
                waiver_activation_eligible = bool(
                    waiver_next3 is not None
                    and math.isfinite(float(waiver_next3))
                    and waiver_feature_coverage >= args.min_feature_coverage
                )
            except Exception:
                waiver_next3 = None
                waiver_feature_coverage = 0.0
                waiver_activation_eligible = False

        confidence = int(round(max(5, min(95, 35 + feature_coverage * 60)))) if weekly_activation_eligible else int(round(max(5, min(60, 10 + feature_coverage * 40))))
        live_features = current_player_features(g, team_hist, team, opponent, comp.get((str(cid), pos), {})) if not g.empty else {}
        players.append({
            "sleeper_id": sid, "canonical_player_id": cid, "full_name": name.strip() or None,
            "team": team or None, "opponent": opponent, "position_model": pos,
            "season": season, "week": week, "history_games": history_games,
            # Backwards-compatible alias for clients written before M5 decision
            # gates became independent.
            "activation_eligible": weekly_activation_eligible,
            "weekly_activation_eligible": weekly_activation_eligible,
            "waiver_activation_eligible": waiver_activation_eligible,
            "projection_source": source,
            "decision_weekly_projection": round(float(decision), 4) if decision is not None and math.isfinite(float(decision)) else None,
            "fie_weekly_projection": round(float(fie_fp), 4) if fie_fp is not None and math.isfinite(float(fie_fp)) else None,
            "sleeper_weekly_projection": round(float(sleeper_fp), 4) if sleeper_fp is not None and math.isfinite(float(sleeper_fp)) else None,
            "p10": round(float(p10), 4) if p10 is not None else None,
            "p90": round(float(p90), 4) if p90 is not None else None,
            "waiver_next3_projection": round(float(waiver_next3), 4) if waiver_next3 is not None and waiver_activation_eligible else None,
            "waiver_feature_coverage": round(float(waiver_feature_coverage), 4),
            "young_role_probability": None, "spike_probability": None, "bust_probability": None,
            "confidence": confidence, "feature_coverage": round(float(feature_coverage), 4),
            "current_features": live_features,
            "predicted_stats": {k: round(float(v), 4) for k, v in fie_stats.items()} if fie_stats else {},
        })

    dst_rows = [r for r in players if r.get("position_model") == "DEF"]
    for rank, r in enumerate(sorted(dst_rows, key=lambda z: (z.get("decision_weekly_projection") is not None, z.get("decision_weekly_projection") or -1e9), reverse=True), 1):
        r["dst_week_rank"] = rank
    for rank, r in enumerate(sorted([z for z in dst_rows if z.get("waiver_next3_projection") is not None], key=lambda z: z.get("waiver_next3_projection") or -1e9, reverse=True), 1):
        r["dst_next3_rank"] = rank
    kicker_rows = [r for r in players if r.get("position_model") == "K"]
    for rank, r in enumerate(sorted(kicker_rows, key=lambda z: (z.get("decision_weekly_projection") is not None, z.get("decision_weekly_projection") or -1e9), reverse=True), 1):
        r["kicker_week_rank"] = rank
    for rank, r in enumerate(sorted([z for z in kicker_rows if z.get("waiver_next3_projection") is not None], key=lambda z: z.get("waiver_next3_projection") or -1e9, reverse=True), 1):
        r["kicker_next3_rank"] = rank

    eligible = sum(1 for r in players if r["weekly_activation_eligible"])
    waiver_eligible = sum(1 for r in players if r.get("waiver_activation_eligible"))
    status = "complete" if players else "ready"
    bundle = {
        "schema_version": 3, "m5_build": M5_BUILD, "producer_build": PRODUCER_BUILD,
        "generated_at": generated, "status": status, "season": season, "week": week,
        "season_type": season_type, "sleeper_state_week": sleeper_week,
        "analysis_week_policy": "explicit --week when supplied; otherwise preseason maps to upcoming regular Week 1",
        "league_id": league_id, "league_format": profile.get("format") if profile else None,
        "profile_fingerprint": profile_fp, "profile_scoring_signature": profile_sig,
        "live_profile_fingerprint": live_profile_fp, "profile_current_match": profile_current_match, "profile_diff": profile_diff,
        "scoring_signature": sig, "scoring_settings": scoring, "scoring_provenance": scoring_prov,
        "scoring_support_relevant": scoring_support_relevant,
        "research_compatible": research_compatible, "snapshot_max_age_hours": 18,
        "target_week_realised_stats_excluded": True,
        "players": players,
        "summary": {
            "players": len(players),
            "activation_eligible": eligible,
            "weekly_activation_eligible": eligible,
            "waiver_activation_eligible": waiver_eligible,
            "fie_projected": sum(r["fie_weekly_projection"] is not None for r in players),
            "sleeper_projected": sum(r["sleeper_weekly_projection"] is not None for r in players),
            "current_features_available": sum(bool((r.get("current_features") or {}).get("values")) for r in players),
            "dst": {"enabled": bool(dst_meta.get("dst_enabled")), "starter_slots": int(dst_meta.get("dst_starter_slots") or 0), "entities": len(dst_rows), "weekly_active": sum(bool(r.get("weekly_activation_eligible")) for r in dst_rows), "waiver_active": sum(bool(r.get("waiver_activation_eligible")) for r in dst_rows), "scoring_signature": dst_meta.get("dst_scoring_signature")},
            "kicker": {"enabled": bool(kicker_meta.get("kicker_enabled")), "starter_slots": int(kicker_meta.get("kicker_starter_slots") or 0), "entities": len(kicker_rows), "weekly_active": sum(bool(r.get("weekly_activation_eligible")) for r in kicker_rows), "waiver_active": sum(bool(r.get("waiver_activation_eligible")) for r in kicker_rows), "scoring_signature": kicker_meta.get("kicker_scoring_signature")},
        },
        "source_health": source_meta, "sleeper_archive": archive_meta,
        "kickoff": {
            "first_kickoff_utc": kickoff.isoformat() if kickoff else None,
            "capture_pregame_eligible": pregame_eligible,
            "capture_policy": capture_decision,
        },
        "guardrails": [
            "No target-week realised stats are used in target-week FIE features.",
            "Player models require at least two completed prior games; D/ST and K use separately validated team-week priors so Week 1 is possible without fabricating current-season history.",
            "M4 weekly model and M5 weekly decision gate must both validate the position for weekly activation.",
            "Waiver next-3 activation is independently gated by M5 waiver validation and live feature coverage.",
            "Scoring signature must match the empirical M5 research profile.",
            "A player model may activate only when every non-zero scoring rule relevant to that player position is replay-supported; irrelevant K/DST rules do not gate offensive-only leagues.",
            "League ID and profile fingerprint must match M4/M5/M6 artifacts when a league profile is supplied.",
            "Current Sleeper roster/settings fingerprint must still match the historical League-ID profile.",
            "Immutable Sleeper benchmarks are written only in regular season and within 18 hours before first kickoff.",
            "Sleeper preseason week numbers never masquerade as regular-season weekly decision weeks.",
        ],
    }
    return bundle


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build FIE V8.8-M6 current-season decision snapshot")
    p.add_argument("--league-id", default=None)
    p.add_argument("--league-profile", default=None, help="League-ID profile.json used to validate namespace/scoring identity")
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
