#!/usr/bin/env python3
"""FIE M9.1 research-only season challenger.

Purpose
-------
M9.1 tests a safer preseason comparison architecture without changing M9 production:

1. Sleeper remains the fixed external baseline.
2. The old single position-wide mean offset is replaced by a robust, monotonic
   position distribution anchor. Current-year M9.1 may reallocate players within
   the Sleeper position distribution, but it may not manufacture a position-wide
   level/dispersion edge before historical Sleeper residual validation exists.
3. A FIE-vs-Sleeper disagreement is emitted only when FIE can replay the league
   scoring exactly and the position distribution anchor has sufficient support.
   Partial scoring never masquerades as a total projection.
4. Team changes no longer invalidate the whole player at QB/RB/WR/TE. Portable player history is
   retained; team/role context is rebuilt from the player's *new* team.
5. Team-change uncertainty is widened only by an empirically estimated historical
   transition-volatility factor from the league-scored player-week history.
6. The true learned target Actual - Sleeper preseason projection remains BLOCKED
   until enough immutable point-in-time Sleeper preseason seasons exist.

This file is a research challenger. It has no promotion or runtime write path.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import numpy as np
import pandas as pd

from build_m9_season_board import (
    board as build_m9_board,
    evaluate_position_spec,
    load_json,
    load_market,
    norm_name,
    norm_sleeper_id,
)
from fie_m9 import simulate_player_season
from fie_m7 import add_derived_driver_features
from preseason_projection import add_scoring_completion_columns, _season_target_catalog

OFFENSE = {"QB", "RB", "WR", "TE"}
RESEARCH_BUILD = "M9.1-TRANSITION-AWARE-CHALLENGER"
SCHEMA_VERSION = 1

# These features describe opportunity/role in a team rather than portable
# individual ability. For a team changer the old-team value is never carried.
ROLE_FEATURES = {
    "qb_pass_attempt_share_prior4",
    "qb_rush_share_prior4",
    "inside_5_carry_share_prior4",
    "snap_share_prior4",
    "offense_snap_share_prior4",
    "carry_share_prior4",
    "target_share_prior4",
    "red_zone_carry_share_prior4",
    "red_zone_target_share_prior4",
    "ngs_percent_share_of_intended_air_yards_prior4",
    "off_part_pass_plays_prior4",
    "opportunity_change_score_prior1",
    "backfield_competition_index_prior4",
    "backfield_competitor_count",
    "receiving_competition_index_prior4",
    "receiving_competitor_count",
}

# Team/environment variables can use current new-team market totals first and
# prior-season new-team contextual donors second.
TEAM_ENV_FEATURES = {
    "team_pass_attempts_prior4_team",
    "team_plays_prior4_team",
    "pfr_times_pressured_pct_prior4",
    "pfr_times_sacked_prior4",
}

# Context-like patterns not explicitly mapped are cleared rather than leaking
# old-team information. Explicit exact-feature mappings below take precedence.
CONTEXT_PATTERNS = (
    "_share_prior",
    "competition_",
    "competitor_count",
    "team_",
    "red_zone_",
    "inside_5_",
    "snap_share",
    "off_part_pass",
)


def _num(x: Any) -> Optional[float]:
    try:
        y = float(x)
        return y if math.isfinite(y) else None
    except Exception:
        return None


def _safe_div(a: Any, b: Any) -> Optional[float]:
    x, y = _num(a), _num(b)
    if x is None or y is None or y <= 0:
        return None
    return x / y


def latest_market_snapshot(root: Path, season: int) -> Path:
    d = root / str(season)
    files = sorted(d.glob("season_market_*.jsonl.gz"))
    if not files:
        raise SystemExit(f"No immutable Sleeper season market snapshot found under {d}")
    return files[-1]


def _stat(rec: dict, *keys: str) -> float:
    stats = rec.get("stats") or {}
    for k in keys:
        x = _num(stats.get(k))
        if x is not None:
            return x
    return 0.0


def build_current_team_context(market: list[dict], games: int) -> tuple[dict, dict]:
    """Build current/new-team context from the baseline's raw projected components.

    We deliberately use Sleeper component projections here because Sleeper is the
    agreed baseline. M9.1 later has to prove that its football correction adds value
    *conditional on* that baseline; it does not second-guess the baseline itself.
    """
    team = {}
    players = {}
    for r in market:
        pos = str(r.get("position_model") or "").upper()
        tm = str(r.get("team") or "")
        cid = str(r.get("canonical_player_id") or "")
        if pos not in OFFENSE or not tm:
            continue
        p_att = _stat(r, "pass_att")
        rush_att = _stat(r, "rush_att")
        tgt = _stat(r, "rec_tgt")
        air = _stat(r, "rec_air_yd", "rec_air_yards", "air_yd")
        z = team.setdefault(tm, {
            "qb_pass_att": 0.0, "rush_att": 0.0, "targets": 0.0,
            "air_yards": 0.0, "rb_rushers": 0, "receivers": 0,
        })
        if pos == "QB":
            z["qb_pass_att"] += p_att
        z["rush_att"] += rush_att
        if pos in {"RB", "WR", "TE"}:
            z["targets"] += tgt
            z["air_yards"] += air
            if tgt > 0:
                z["receivers"] += 1
        if pos == "RB" and rush_att > 0:
            z["rb_rushers"] += 1
        players[cid] = {
            "team": tm, "position": pos, "pass_att": p_att,
            "rush_att": rush_att, "targets": tgt, "air_yards": air,
        }

    out = {}
    for cid, p in players.items():
        z = team[p["team"]]
        pos = p["position"]
        vals = {
            "team_pass_attempts_prior4_team": z["qb_pass_att"] / max(1, games),
            "team_plays_prior4_team": (z["qb_pass_att"] + z["rush_att"]) / max(1, games),
        }
        if pos == "QB":
            vals["qb_pass_attempt_share_prior4"] = _safe_div(p["pass_att"], z["qb_pass_att"])
            vals["qb_rush_share_prior4"] = _safe_div(p["rush_att"], z["rush_att"])
        if pos == "RB":
            carry_share = _safe_div(p["rush_att"], z["rush_att"])
            target_share = _safe_div(p["targets"], z["targets"])
            vals["carry_share_prior4"] = carry_share
            vals["target_share_prior4"] = target_share
            vals["backfield_competitor_count"] = float(max(0, z["rb_rushers"] - 1))
            if carry_share is not None:
                vals["backfield_competition_index_prior4"] = float(max(0.0, min(1.0, 1.0 - carry_share)))
        if pos in {"WR", "TE"}:
            target_share = _safe_div(p["targets"], z["targets"])
            vals["target_share_prior4"] = target_share
            vals["receiving_competitor_count"] = float(max(0, z["receivers"] - 1))
            if target_share is not None:
                vals["receiving_competition_index_prior4"] = float(max(0.0, min(1.0, 1.0 - target_share)))
        if pos in {"RB", "WR", "TE"}:
            vals["ngs_percent_share_of_intended_air_yards_prior4"] = _safe_div(p["air_yards"], z["air_yards"])
        out[cid] = {k: v for k, v in vals.items() if v is not None}
    return out, team


def build_market_record_index(market: list[dict]) -> dict[str, dict]:
    return {
        str(r.get("canonical_player_id") or ""): r
        for r in market
        if r.get("canonical_player_id")
    }


def sleeper_return_context(rec: dict) -> dict:
    """Use current Sleeper return projections as current-team opportunity context.

    Return opportunity is team/role dependent. We therefore never carry an old-team
    FIE return-role projection across a move. If Sleeper does not expose the active
    return components, exact replay can remain blocked for that scoring format, but
    the block reason is missing scoring data rather than TEAM_CHANGE.
    """
    stats = (rec or {}).get("stats") or {}
    out = {}
    aliases = {
        "kr_yd": ("kr_yd", "kick_ret_yd"),
        "pr_yd": ("pr_yd", "punt_ret_yd"),
        "kr_td": ("kr_td", "kick_ret_td"),
        "pr_td": ("pr_td", "punt_ret_td"),
    }
    for dest, keys in aliases.items():
        for k in keys:
            x = _num(stats.get(k))
            if x is not None:
                out[dest] = x
                break
    if out:
        out["return_yd"] = float(out.get("kr_yd", 0.0) or 0.0) + float(out.get("pr_yd", 0.0) or 0.0)
        out["return_td"] = float(out.get("kr_td", 0.0) or 0.0) + float(out.get("pr_td", 0.0) or 0.0)
    return out


def empirical_position_anchor(df: pd.DataFrame, *, min_reference: int = 12) -> tuple[pd.Series, pd.DataFrame]:
    """Map the raw FIE ordering onto the Sleeper position distribution.

    Why this instead of no centering:
      - a raw FIE model can have a systematic level and dispersion bias;
      - a single mean offset fixes level only and is outlier-sensitive;
      - empirical quantile anchoring fixes level *and* dispersion/shape while
        preserving the football model's ordering signal.

    Stable-team exact-replay rows are preferred as the reference distribution so
    team-transition uncertainty does not define the calibration itself. When the
    stable reference is too small, all exact-replay rows may be used. If the
    position still lacks support, the challenger stays at Sleeper.

    This is intentionally market-neutral research calibration. Once historical
    point-in-time Sleeper baselines exist, a validated residual model can replace
    it and may legitimately move the aggregate position point level.
    """
    result = pd.Series(np.nan, index=df.index, dtype=float)
    audit_rows = []
    for pos, idx in df.groupby("position_model").groups.items():
        g = df.loc[list(idx)].copy()
        raw = pd.to_numeric(g["m91_raw_fie_projection"], errors="coerce")
        mkt = pd.to_numeric(g["sleeper_market_projection"], errors="coerce")
        exact = g["m91_exact_scoring_replay"].fillna(False).astype(bool)
        teamchg = g["team_changed"].fillna(False).astype(bool)
        base = exact & raw.notna() & mkt.notna() & mkt.gt(0)
        stable = base & ~teamchg

        ref_mask = stable if int(stable.sum()) >= min_reference else base
        ref_kind = "STABLE_TEAM_EXACT_REPLAY" if ref_mask is stable else "ALL_EXACT_REPLAY"
        ref_raw = raw[ref_mask].sort_values().to_numpy(dtype=float)
        ref_mkt = mkt[ref_mask].sort_values().to_numpy(dtype=float)

        if len(ref_raw) < min_reference:
            audit_rows.append({
                "position_model": pos,
                "status": "INSUFFICIENT_DISTRIBUTION_REFERENCE",
                "reference_kind": ref_kind,
                "reference_n": int(len(ref_raw)),
            })
            continue

        n = len(ref_raw)
        # Mid-rank empirical CDF, then interpolate the corresponding Sleeper
        # empirical quantile. Ties remain monotonic and no cross-position pooling.
        qgrid = (np.arange(n, dtype=float) + 0.5) / n

        def map_one(x: float) -> tuple[float, float]:
            left = np.searchsorted(ref_raw, x, side="left")
            right = np.searchsorted(ref_raw, x, side="right")
            rank = (left + right) / 2.0
            q = min(1.0, max(0.0, (rank + 0.5) / n))
            y = float(np.interp(q, qgrid, ref_mkt, left=ref_mkt[0], right=ref_mkt[-1]))
            return y, q

        for ridx in g.index[base]:
            y, q = map_one(float(raw.loc[ridx]))
            result.loc[ridx] = y
            df.loc[ridx, "m91_calibration_percentile"] = q
            df.loc[ridx, "m91_distribution_anchor_applied"] = True
            df.loc[ridx, "m91_calibration_reference_kind"] = ref_kind
            df.loc[ridx, "m91_calibration_reference_n"] = int(n)

        audit_rows.append({
            "position_model": pos,
            "status": "POSITION_EMPIRICAL_QUANTILE_ANCHOR",
            "reference_kind": ref_kind,
            "reference_n": int(n),
            "raw_median": float(np.median(ref_raw)),
            "sleeper_median": float(np.median(ref_mkt)),
            "raw_mean": float(np.mean(ref_raw)),
            "sleeper_mean": float(np.mean(ref_mkt)),
        })
    return result, pd.DataFrame(audit_rows)


def required_features(spec: dict) -> set[str]:
    return {
        str(f)
        for target in (spec.get("targets") or [])
        for f in (target.get("features") or [])
    }


def new_team_donor_values(profiles: pd.DataFrame, team: str, pos: str, features: Iterable[str]) -> dict:
    if profiles.empty:
        return {}
    z = profiles[
        profiles.get("profile_team", pd.Series("", index=profiles.index)).astype(str).eq(str(team))
        & profiles.get("position_model", pd.Series("", index=profiles.index)).astype(str).str.upper().eq(pos)
    ].copy()
    if z.empty:
        return {}
    out = {}
    for f in features:
        if f not in z:
            continue
        x = pd.to_numeric(z[f], errors="coerce").dropna()
        if not x.empty:
            out[f] = float(x.median())
    return out


def is_context_feature(name: str) -> bool:
    if name in ROLE_FEATURES or name in TEAM_ENV_FEATURES:
        return True
    return any(token in name for token in CONTEXT_PATTERNS)


def adapt_profile_for_new_team(
    profile: dict,
    *,
    cid: str,
    pos: str,
    current_team: str,
    spec: dict,
    market_context: dict,
    profiles: pd.DataFrame,
) -> tuple[dict, dict]:
    """Retain portable player signal; rebuild/clear team-sensitive features."""
    old_team = str(profile.get("profile_team") or "")
    changed = bool(current_team and old_team and current_team != old_team)
    if not changed:
        return dict(profile), {
            "team_changed": False, "status": "STABLE_TEAM",
            "replaced_current_market": [], "replaced_new_team_history": [],
            "cleared_old_team_context": [], "portable_retained": [],
        }

    adapted = dict(profile)
    feats = required_features(spec)
    current = market_context.get(str(cid), {})
    donor = new_team_donor_values(profiles, current_team, pos, feats)
    audit = {
        "team_changed": True,
        "status": "NEW_TEAM_CONTEXT_REBUILT",
        "from_team": old_team,
        "to_team": current_team,
        "replaced_current_market": [],
        "replaced_new_team_history": [],
        "cleared_old_team_context": [],
        "portable_retained": [],
    }

    for f in feats:
        if not is_context_feature(f):
            audit["portable_retained"].append(f)
            continue

        # Current new-team projected role/environment is preferred.
        if f in current and _num(current[f]) is not None:
            adapted[f] = float(current[f])
            audit["replaced_current_market"].append(f)
            continue

        # Role fields must not borrow an incumbent's prior-season role.
        if f in ROLE_FEATURES:
            adapted[f] = np.nan
            audit["cleared_old_team_context"].append(f)
            continue

        # Team environment may use the same-position prior-season new-team donor.
        if f in donor and _num(donor[f]) is not None:
            adapted[f] = float(donor[f])
            audit["replaced_new_team_history"].append(f)
            continue

        adapted[f] = np.nan
        audit["cleared_old_team_context"].append(f)

    adapted["profile_team"] = current_team
    return adapted, audit


def transition_volatility(player_week_path: Path) -> dict:
    """Historical team-change instability using completed player seasons only.

    This is not a Sleeper-residual calibration. It only estimates whether changing
    teams has historically increased year-to-year fantasy PPG volatility.
    """
    if not player_week_path.is_file():
        return {}
    d = pd.read_csv(player_week_path, low_memory=False)
    need = {"canonical_player_id", "season", "team", "position_model", "fantasy_points"}
    if not need.issubset(d.columns):
        return {}
    d = d[d.position_model.astype(str).str.upper().isin(OFFENSE)].copy()
    d["fantasy_points"] = pd.to_numeric(d.fantasy_points, errors="coerce")
    d["season"] = pd.to_numeric(d.season, errors="coerce")
    d = d.dropna(subset=["canonical_player_id", "season", "fantasy_points"])
    rows = []
    for (pid, season), g in d.groupby(["canonical_player_id", "season"]):
        if len(g) < 4:
            continue
        team_counts = g.team.astype(str).value_counts()
        rows.append({
            "canonical_player_id": str(pid), "season": int(season),
            "position_model": str(g.position_model.iloc[0]).upper(),
            "team": str(team_counts.index[0]) if len(team_counts) else "",
            "ppg": float(g.fantasy_points.mean()), "games": int(len(g)),
        })
    s = pd.DataFrame(rows)
    if s.empty:
        return {}
    s = s.sort_values(["canonical_player_id", "season"])
    prev = s.rename(columns={
        "season": "prev_season", "team": "prev_team", "ppg": "prev_ppg",
        "games": "prev_games", "position_model": "prev_position",
    })
    cur = s.rename(columns={
        "season": "cur_season", "team": "cur_team", "ppg": "cur_ppg",
        "games": "cur_games", "position_model": "cur_position",
    })
    x = prev.merge(cur, on="canonical_player_id")
    x = x[x.cur_season.eq(x.prev_season + 1) & x.cur_position.eq(x.prev_position)].copy()
    x["team_changed"] = x.prev_team.ne(x.cur_team)
    x["abs_delta"] = (x.cur_ppg - x.prev_ppg).abs()

    out = {}
    for pos, g in x.groupby("cur_position"):
        a = g[g.team_changed].abs_delta.dropna()
        b = g[~g.team_changed].abs_delta.dropna()
        record = {
            "changed_n": int(len(a)), "stable_n": int(len(b)),
            "changed_median_abs_ppg_delta": float(a.median()) if len(a) else None,
            "stable_median_abs_ppg_delta": float(b.median()) if len(b) else None,
            "status": "INSUFFICIENT_HISTORY",
            "spread_multiplier": 1.0,
        }
        if len(a) >= 20 and len(b) >= 50 and float(b.median()) > 1e-9:
            ratio = float(a.median() / b.median())
            record["raw_ratio"] = ratio
            # Safety cap only prevents a sparse/extreme historical tail from exploding
            # report intervals. It never makes a team changer *less* uncertain.
            record["spread_multiplier"] = float(max(1.0, min(2.0, ratio)))
            record["status"] = "EMPIRICAL_TRANSITION_VOLATILITY"
        out[str(pos)] = record
    return out


def market_history_status(market_root: Path, current_season: int) -> dict:
    seasons = []
    if market_root.is_dir():
        for p in market_root.iterdir():
            if p.is_dir() and p.name.isdigit() and list(p.glob("season_market_*.jsonl.gz")):
                seasons.append(int(p.name))
    seasons = sorted(set(seasons))
    completed = [s for s in seasons if s < current_season]
    return {
        "available_seasons": seasons,
        "completed_seasons_with_immutable_preseason_market": completed,
        "required_completed_seasons": 4,
        "status": "READY_FOR_RESIDUAL_RESEARCH" if len(completed) >= 4 else "BLOCKED_MISSING_HISTORICAL_SLEEPER_BASELINE",
        "semantics": "Future residual target is actual league-scored season points minus point-in-time Sleeper preseason projection.",
    }


def _first_numeric(df: pd.DataFrame, names: Iterable[str]) -> Optional[str]:
    for name in names:
        if name in df.columns and pd.to_numeric(df[name], errors="coerce").notna().any():
            return str(name)
    return None


def rehydrate_latest_profiles(
    *,
    player_week_path: Path,
    m9: dict,
    output_path: Path,
) -> pd.DataFrame:
    """Reconstruct M9's latest preseason profile table from canonical player-week.

    The committed M9 bundle contains the trained target specifications and therefore
    defines the required profile features. The missing `.cache` artifact is only a
    deterministic feature table derived from completed-season player-week history.

    This function does NOT refit M9, alter coefficients, rerun M4/M7/M8, or require
    OOS cache artifacts. It recreates the exact type of latest player profile that
    the committed M9 specs consume.
    """
    if not player_week_path.is_file():
        raise SystemExit(f"M9.1 cannot rehydrate profiles; missing {player_week_path}")

    df = pd.read_csv(player_week_path, low_memory=False)
    required = {"canonical_player_id", "season", "week", "position_model", "fantasy_points"}
    if not required.issubset(df.columns):
        raise SystemExit(f"M9.1 player-week cache missing required columns: {sorted(required-set(df.columns))}")

    df = add_scoring_completion_columns(df)
    df = add_derived_driver_features(df)

    preseason = m9.get("preseason_season_projection", {}) or {}
    specs = preseason.get("diagnostic_model_specs", {}) or preseason.get("model_specs", {}) or {}
    rows = []

    for pos in sorted(OFFENSE):
        pspec = specs.get(pos) or {}
        if not pspec:
            continue
        dpos = df[df.position_model.astype(str).str.upper().eq(pos)].copy()
        if dpos.empty:
            continue
        seasons = pd.to_numeric(dpos["season"], errors="coerce").dropna()
        if seasons.empty:
            continue
        max_season = int(seasons.max())
        latest = dpos[pd.to_numeric(dpos["season"], errors="coerce").eq(max_season)].copy()
        if latest.empty:
            continue

        # Use the committed spec as the authoritative feature contract.
        features = sorted({
            str(f)
            for target in (pspec.get("targets") or [])
            for f in (target.get("features") or [])
            if str(f) not in {"prev_fantasy_ppg"}
        })

        target_sources = {}
        catalog = _season_target_catalog(pos)
        target_names = {
            str(t.get("target"))
            for t in (pspec.get("targets") or [])
            if t.get("target")
        }
        for target in target_names:
            aliases = catalog.get(target) or [target]
            source = _first_numeric(latest, aliases)
            if source:
                target_sources[target] = source

        for pid, g in latest.sort_values("week").groupby("canonical_player_id", sort=False):
            g = g.sort_values("week")
            last = g.iloc[-1]
            fp = pd.to_numeric(g["fantasy_points"], errors="coerce")
            row = {
                "canonical_player_id": str(pid),
                "profile_season": max_season,
                "full_name": last.get("full_name"),
                "profile_team": last.get("team"),
                "position_model": pos,
                "prev_fantasy_ppg": float(fp.mean()) if fp.notna().any() else np.nan,
                "prev_games": int(fp.notna().sum()),
            }
            for f in features:
                x = _num(last.get(f))
                row[f] = float(x) if x is not None else np.nan
            for target, source in target_sources.items():
                vals = pd.to_numeric(g[source], errors="coerce")
                row[f"prev__{target}"] = float(vals.mean()) if vals.notna().any() else np.nan
            rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        raise SystemExit("M9.1 latest-profile rehydration produced no offensive player profiles")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False, compression="gzip" if output_path.suffix == ".gz" else None)
    return out


def _profiles(
    m9: dict,
    *,
    override: str = "",
    player_week_path: Optional[Path] = None,
    rehydrated_output: Optional[Path] = None,
) -> tuple[pd.DataFrame, Path, str]:
    preseason = m9.get("preseason_season_projection", {}) or {}
    p = Path(override or preseason.get("latest_profiles_derived_table") or "")
    if p and not p.is_absolute():
        p = Path.cwd() / p
    if p and p.is_file():
        return pd.read_csv(p, low_memory=False), p, "EXISTING_M9_DERIVED_PROFILE"

    if player_week_path is None:
        raise SystemExit(f"M9.1 requires a preseason profile table or player-week cache; missing configured path {p}")
    out = rehydrated_output or (player_week_path.parent / "m9_preseason_latest_profiles_rehydrated.csv.gz")
    df = rehydrate_latest_profiles(player_week_path=player_week_path, m9=m9, output_path=out)
    return df, out, "REHYDRATED_FROM_CANONICAL_PLAYER_WEEK_AND_COMMITTED_M9_SPEC"


def build(args) -> tuple[pd.DataFrame, dict]:
    league_root = Path("data/research/leagues") / str(args.league_id)
    m1_path = league_root / "milestone1.json"
    m9_path = league_root / "milestone9.json"
    if not m1_path.is_file() or not m9_path.is_file():
        raise SystemExit("M9.1 requires canonical milestone1.json and milestone9.json")

    market_root = Path(args.market_root)
    market_path = Path(args.market_snapshot) if args.market_snapshot else latest_market_snapshot(market_root, args.season)
    m9 = load_json(str(m9_path))
    player_week_path = Path(args.player_week) if args.player_week else Path(".cache/fie-research/leagues") / str(args.league_id) / "derived" / "player_week.csv.gz"
    profiles, profile_path, profile_source = _profiles(
        m9,
        override=args.profile_table,
        player_week_path=player_week_path,
        rehydrated_output=player_week_path.parent / "m9_preseason_latest_profiles_rehydrated.csv.gz",
    )
    if profiles.empty:
        raise SystemExit(f"M9.1 requires latest preseason profiles; rehydration failed at {profile_path}")

    market = load_market(str(market_path))
    market_ctx, _ = build_current_team_context(market, args.games)
    market_by_cid = build_market_record_index(market)
    scoring = (load_json(str(m1_path)).get("scoring") or {}).get("settings", {})

    # Build existing M9 board in memory for exact identity joins, current quantile
    # spreads, and side-by-side audit. This does not write or mutate M9.
    ns = argparse.Namespace(
        m1_bundle=str(m1_path), m9_bundle=str(m9_path), market_snapshot=str(market_path),
        profile_table=str(profile_path), adp_key=args.adp_key, games=args.games,
        simulations=args.simulations, seed=args.seed, active_probability=args.active_probability,
        output="",
    )
    base = build_m9_board(ns)
    by_pid = {
        str(r["canonical_player_id"]): r
        for r in profiles.to_dict("records")
        if r.get("canonical_player_id") is not None
    }
    preseason = m9.get("preseason_season_projection", {}) or {}
    specs = preseason.get("diagnostic_model_specs", {}) or preseason.get("model_specs", {}) or {}
    weekly_cal = m9.get("projection_distribution", {}).get("position_calibration", {}) or {}
    volatility = transition_volatility(player_week_path)
    hist = market_history_status(market_root, args.season)

    rows = []
    for i, r in base.iterrows():
        row = dict(r)
        pos = str(row.get("position_model") or "").upper()
        cid = str(row.get("canonical_player_id") or "")
        current_team = str(row.get("team") or "")
        profile = by_pid.get(cid)
        spec = specs.get(pos) or {}
        market_pts = _num(row.get("sleeper_market_projection"))

        status = "BASELINE_ONLY"
        raw_mean = None
        audit = {"team_changed": bool(row.get("team_changed")), "status": "NO_PROFILE"}
        exact = False
        if profile and spec and market_pts is not None:
            adapted, audit = adapt_profile_for_new_team(
                profile, cid=cid, pos=pos, current_team=current_team, spec=spec,
                market_context=market_ctx, profiles=profiles,
            )
            return_ctx = sleeper_return_context(market_by_cid.get(cid, {}))
            ev = evaluate_position_spec(spec, adapted, scoring, pos, return_raw=return_ctx)
            exact = bool((ev.get("coverage") or {}).get("exact_linear_replay"))
            ppg = _num(ev.get("ppg"))
            if exact and ppg is not None:
                raw_mean = ppg * args.games
                status = "RESEARCH_ONLY_EXACT_REPLAY"
                if audit.get("team_changed"):
                    status = "RESEARCH_ONLY_TRANSITION_ADJUSTED_EXACT_REPLAY"
            else:
                status = "BASELINE_ONLY_PARTIAL_SCORING"

        # The raw exact-replay model is retained for audit, but final current-year
        # M9.1 projection is assigned only after a position distribution anchor is
        # estimated across the complete board. This avoids both the old blunt mean
        # offset and the opposite mistake of trusting an uncalibrated raw point level.
        challenger = market_pts
        delta = None

        # Preserve M9's empirically calibrated position spread. For team changers,
        # widen only by a historically measured transition-volatility ratio.
        spread_mult = 1.0
        vol = volatility.get(pos, {})
        if bool(audit.get("team_changed")):
            spread_mult = float(vol.get("spread_multiplier") or 1.0)

        qout = {}
        base_center = _num(row.get("fie_season_mean")) or market_pts
        if challenger is not None and base_center is not None:
            for qn in ("p10", "p25", "p50", "p75", "p90"):
                qv = _num(row.get(qn))
                if qv is not None:
                    qout[f"m91_{qn}"] = challenger + (qv - base_center) * spread_mult
                else:
                    qout[f"m91_{qn}"] = None
        else:
            qout = {f"m91_{q}": None for q in ("p10","p25","p50","p75","p90")}

        rows.append({
            **row,
            "m91_research_build": RESEARCH_BUILD,
            "m91_status": status,
            "m91_projection": challenger,
            "m91_raw_fie_projection": raw_mean,
            "m91_delta_vs_sleeper": delta,
            "m91_delta_pct_vs_sleeper": None,
            "m91_raw_delta_vs_sleeper": (raw_mean - market_pts) if raw_mean is not None and market_pts is not None else None,
            "m91_mean_centering_applied": False,
            "m91_distribution_anchor_applied": False,
            "m91_calibration_method": "PENDING_POSITION_EMPIRICAL_QUANTILE_ANCHOR" if exact else "BASELINE_ONLY",
            "m91_calibration_percentile": None,
            "m91_calibration_reference_kind": None,
            "m91_calibration_reference_n": 0,
            "m91_exact_scoring_replay": exact,
            "m91_team_transition_status": audit.get("status"),
            "m91_new_team_current_context_fields": "|".join(audit.get("replaced_current_market") or []),
            "m91_new_team_history_fields": "|".join(audit.get("replaced_new_team_history") or []),
            "m91_cleared_old_team_context_fields": "|".join(audit.get("cleared_old_team_context") or []),
            "m91_portable_retained_count": len(audit.get("portable_retained") or []),
            "m91_uncertainty_spread_multiplier": spread_mult,
            "m91_uncertainty_status": vol.get("status") if audit.get("team_changed") else "STANDARD_M9_POSITION_CALIBRATION",
            "m91_residual_gate": hist["status"],
            "m91_production_eligible": False,
            **qout,
        })

    out = pd.DataFrame(rows)
    calibration = pd.DataFrame()
    if not out.empty:
        anchored, calibration = empirical_position_anchor(out)
        eligible_anchor = anchored.notna()
        out.loc[eligible_anchor, "m91_projection"] = anchored[eligible_anchor]
        out.loc[eligible_anchor, "m91_calibration_method"] = "POSITION_EMPIRICAL_QUANTILE_ANCHOR"
        mkt = pd.to_numeric(out["sleeper_market_projection"], errors="coerce")
        proj = pd.to_numeric(out["m91_projection"], errors="coerce")
        out["m91_delta_vs_sleeper"] = proj - mkt
        out["m91_delta_pct_vs_sleeper"] = np.where(mkt.abs() > 1e-9, (proj - mkt) / mkt.abs() * 100.0, np.nan)

        # Recenter existing M9 position uncertainty around the now-calibrated M9.1
        # point estimate. Team changers retain the empirical spread multiplier.
        base_center = pd.to_numeric(out["fie_season_mean"], errors="coerce")
        fallback_center = mkt
        center = base_center.where(base_center.notna(), fallback_center)
        for qn in ("p10","p25","p50","p75","p90"):
            baseq = pd.to_numeric(out[qn], errors="coerce")
            spread = (baseq - center) * pd.to_numeric(out["m91_uncertainty_spread_multiplier"], errors="coerce").fillna(1.0)
            out[f"m91_{qn}"] = proj + spread

        out["m91_position_rank"] = out.groupby("position_model")["m91_projection"].rank(method="min", ascending=False)
        out["m91_market_position_rank"] = out.groupby("position_model")["sleeper_market_projection"].rank(method="min", ascending=False)
        out["m91_rank_delta_vs_market"] = out["m91_market_position_rank"] - out["m91_position_rank"]

    meta = {
        "schema_version": SCHEMA_VERSION,
        "research_build": RESEARCH_BUILD,
        "league_id": str(args.league_id),
        "season": int(args.season),
        "status": "RESEARCH_ONLY_BLOCKED_PROMOTION",
        "production_eligible": False,
        "automatic_promotion": False,
        "sleeper_is_fixed_baseline": True,
        "single_mean_centering_applied": False,
        "distribution_anchor": {
            "method": "POSITION_EMPIRICAL_QUANTILE_ANCHOR",
            "purpose": "market-neutral current-year calibration of raw FIE level, dispersion and shape before historical Sleeper residual validation",
            "preferred_reference": "stable-team exact-replay players",
            "minimum_reference_n": 12,
            "per_position": calibration.to_dict("records") if not calibration.empty else [],
        },
        "team_transition_policy": {
            "portable_player_features": "retained",
            "team_dependent_features": "replace from current new-team Sleeper component context first; prior-season new-team environment second; otherwise clear old-team value",
            "applies_to_positions": ["QB", "RB", "WR", "TE"],
            "team_change_is_never_a_block_reason": True,
            "old_team_context_carried": False,
        },
        "residual_model_gate": hist,
        "transition_volatility": volatility,
        "market_snapshot": str(market_path),
        "profile_table": str(profile_path),
        "profile_source": profile_source,
        "profile_rehydration_refit": False,
        "rows": int(len(out)),
        "exact_replay_rows": int(out.m91_exact_scoring_replay.fillna(False).sum()) if not out.empty else 0,
        "transition_rows": int(out.team_changed.fillna(False).sum()) if not out.empty else 0,
        "notes": [
            "M9 remains production. M9.1 is side-by-side research only.",
            "The old single position-wide mean correction is not used; a position empirical quantile anchor calibrates level, dispersion and shape.",
            "No learned Actual-minus-Sleeper correction is claimed without historical point-in-time Sleeper preseason baselines.",
            "ADP is not used as a football-model feature.",
        ],
    }
    return out, meta


def write_summary(df: pd.DataFrame, meta: dict, path: Path) -> None:
    names = ["Lamar Jackson", "Kyler Murray", "Malik Willis", "Jaylen Waddle", "David Montgomery"]
    q = df[df.full_name.astype(str).isin(names)].copy() if "full_name" in df else pd.DataFrame()
    cols = [
        "full_name","position_model","team","profile_team","team_changed",
        "sleeper_market_projection","fie_diagnostic_mean","diagnostic_center_offset",
        "m91_projection","m91_raw_fie_projection","m91_raw_delta_vs_sleeper","m91_delta_vs_sleeper",
        "m91_calibration_method","m91_calibration_percentile","m91_calibration_reference_n",
        "m91_position_rank","m91_market_position_rank","m91_rank_delta_vs_market",
        "m91_team_transition_status","m91_new_team_current_context_fields",
        "m91_new_team_history_fields","m91_cleared_old_team_context_fields",
        "m91_uncertainty_spread_multiplier","m91_residual_gate",
    ]
    players = [{k: (None if pd.isna(v) else v) for k,v in r.items()} for r in q[[c for c in cols if c in q]].to_dict("records")]
    payload = {**meta, "focus_players": players}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build FIE M9.1 transition-aware research challenger")
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", required=True, type=int)
    p.add_argument("--market-root", default="data/research/market/sleeper")
    p.add_argument("--market-snapshot", default="")
    p.add_argument("--profile-table", default="")
    p.add_argument("--player-week", default="")
    p.add_argument("--adp-key", default="adp_ppr")
    p.add_argument("--games", type=int, default=17)
    p.add_argument("--simulations", type=int, default=10000)
    p.add_argument("--seed", type=int, default=9411)
    p.add_argument("--active-probability", type=float, default=1.0)
    p.add_argument("--output-dir", default="")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    outdir = Path(a.output_dir) if a.output_dir else Path("data/research/leagues") / str(a.league_id) / "performance" / str(a.season) / "m91_challenger"
    outdir.mkdir(parents=True, exist_ok=True)
    df, meta = build(a)
    df.to_csv(outdir / "m91_season_board.csv", index=False)
    (outdir / "m91_meta.json").write_text(json.dumps(meta, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")
    write_summary(df, meta, outdir / "m91_focus_summary.json")
    print(f"Wrote M9.1 challenger: rows={len(df)} exact={meta['exact_replay_rows']} transitions={meta['transition_rows']} residual_gate={meta['residual_model_gate']['status']}")


if __name__ == "__main__":
    main()
