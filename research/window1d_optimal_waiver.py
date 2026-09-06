#!/usr/bin/env python3
"""Window 1D: research-only optimal waiver and Chopped FAAB decision engine.

The engine consumes governed FIE current snapshots plus live Sleeper league state.
It learns bid-price curves only from observable Sleeper waiver transactions and
never invents hidden bids or no-bid behavior. The target week's transactions are
excluded from its own recommendation history to prevent post-auction leakage.

Window 1D is a decision-support layer under data/research/evaluation. It does not
change M9, model weights, canonical rankings, production runtime, or ADP treatment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_HISTORY = "fie-window1d-waiver-history-v1"
SCHEMA_LEAGUE = "fie-window1d-optimal-waiver-v1"
SCHEMA_PORTFOLIO = "fie-window1d-optimal-waiver-portfolio-v1"
CHOPPED_FORMATS = {"CHOPPED", "CHOPPED_BESTBALL"}
NON_STARTER_SLOTS = {"BN", "BENCH", "IR", "RESERVE", "TAXI"}
SLOT_ELIGIBILITY: dict[str, set[str]] = {
    "QB": {"QB"}, "RB": {"RB"}, "WR": {"WR"}, "TE": {"TE"}, "K": {"K"},
    "DEF": {"DEF"}, "DST": {"DEF"}, "DL": {"DL"}, "DE": {"DL"}, "DT": {"DL"},
    "LB": {"LB"}, "DB": {"DB"}, "CB": {"DB"}, "S": {"DB"},
    "FLEX": {"RB", "WR", "TE"}, "WRRB_FLEX": {"RB", "WR"}, "REC_FLEX": {"WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"}, "SUPERFLEX": {"QB", "RB", "WR", "TE"},
    "IDP_FLEX": {"DL", "LB", "DB"}, "IDP_FLEX2": {"DL", "LB", "DB"},
}


class EvidenceError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize_position(value: Any) -> str:
    pos = str(value or "").upper().strip()
    if pos in {"DST", "D/ST"}:
        return "DEF"
    if pos in {"DE", "DT", "EDGE", "IDL"}:
        return "DL"
    if pos in {"CB", "S", "FS", "SS"}:
        return "DB"
    return pos


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def stable_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def http_json(url: str, timeout: int = 25) -> Any:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Fantasy-Intelligence-Window1D/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP_{response.status}:{url}")
        return json.loads(response.read().decode("utf-8"))


def load_current(path: Path, root: Path = ROOT) -> dict[str, Any]:
    try:
        from current_snapshot_storage import load_current_snapshot  # type: ignore
        return load_current_snapshot(path, root=root)
    except ImportError:
        return read_json(path, {}) or {}
    except Exception as exc:
        raise EvidenceError(f"CURRENT_SNAPSHOT_HYDRATION_FAILED:{type(exc).__name__}:{exc}") from exc


def current_index(current: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in current.get("players") or []:
        if not isinstance(row, dict):
            continue
        ids = [row.get("sleeper_id"), row.get("canonical_player_id")]
        if normalize_position(row.get("position_model")) == "DEF" and row.get("team"):
            ids.append(row.get("team"))
        for value in ids:
            if value is None:
                continue
            key = str(value).strip()
            if key and key not in out:
                out[key] = row
    return out


def player_id(row: dict[str, Any]) -> str | None:
    for value in (row.get("sleeper_id"), row.get("player_id"), row.get("canonical_player_id")):
        if value is not None and str(value).strip():
            return str(value).strip()
    if normalize_position(row.get("position_model")) == "DEF" and row.get("team"):
        return str(row.get("team"))
    return None


def player_name(row: dict[str, Any] | None, pid: str) -> str:
    row = row or {}
    for key in ("full_name", "name", "player_name"):
        if row.get(key):
            return str(row[key])
    if normalize_position(row.get("position_model")) == "DEF":
        return f"{row.get('team') or pid} D/ST"
    return pid


def rosterable_positions(profile: dict[str, Any]) -> set[str]:
    slots = [str(x).upper() for x in (profile.get("roster_positions") or []) if str(x).upper() not in NON_STARTER_SLOTS]
    allowed: set[str] = set()
    for slot in slots:
        allowed |= SLOT_ELIGIBILITY.get(slot, {normalize_position(slot)})
    return allowed


def valid_ids(values: Iterable[Any] | None) -> list[str]:
    out: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text != "0" and text not in out:
            out.append(text)
    return out


def starter_slots(profile: dict[str, Any]) -> list[str]:
    return [str(x).upper() for x in (profile.get("roster_positions") or []) if str(x).upper() not in NON_STARTER_SLOTS]


def position_eligible(slot: str, pos: str) -> bool:
    s = str(slot or "").upper()
    p = normalize_position(pos)
    return p in SLOT_ELIGIBILITY.get(s, {normalize_position(s)})


def managed_roster(rosters: list[dict[str, Any]], users: list[dict[str, Any]], username: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    needle = str(username or "").strip().lower()
    matches = [u for u in users if str(u.get("display_name") or u.get("username") or "").strip().lower() == needle]
    if len(matches) != 1:
        return None, None
    user = matches[0]
    uid = str(user.get("user_id") or "")
    owned = [
        r for r in rosters
        if str(r.get("owner_id") or "") == uid or uid in {str(x) for x in (r.get("co_owners") or [])}
    ]
    return (owned[0] if len(owned) == 1 else None), user


def remaining_budget(roster: dict[str, Any], cap: float) -> float:
    settings = roster.get("settings") if isinstance(roster.get("settings"), dict) else {}
    used = numeric(settings.get("waiver_budget_used")) or 0.0
    return max(0.0, float(cap) - used)


def _metadata_text(metadata: Any) -> str:
    if metadata is None:
        return ""
    if isinstance(metadata, str):
        return metadata.lower()
    try:
        return json.dumps(metadata, sort_keys=True).lower()
    except Exception:
        return str(metadata).lower()


def normalize_waiver_transactions(
    transactions: list[dict[str, Any]], *, portfolio_league_id: str, source_league_id: str,
    season: int, week: int, league_format: str, budget_cap: float,
) -> list[dict[str, Any]]:
    """Normalize only bids Sleeper explicitly exposes.

    A failed transaction is preserved as a failed claim. It becomes an explicit
    competitive loss only when Sleeper metadata itself indicates an outbid/higher
    bid reason. Other failures may reflect roster/drop/eligibility problems and
    must not be mislabeled as auction competition.
    """
    out: list[dict[str, Any]] = []
    for tx in transactions or []:
        if not isinstance(tx, dict) or str(tx.get("type") or "").lower() != "waiver":
            continue
        settings = tx.get("settings") if isinstance(tx.get("settings"), dict) else {}
        bid = numeric(settings.get("waiver_bid"))
        if bid is None or bid < 0:
            continue
        adds = tx.get("adds") if isinstance(tx.get("adds"), dict) else {}
        if not adds:
            continue
        status = str(tx.get("status") or "unknown").lower()
        meta = _metadata_text(tx.get("metadata"))
        competitive_loss = bool(status == "failed" and any(token in meta for token in ("outbid", "higher bid", "waiver bid", "bid was")))
        for pid, rid in adds.items():
            out.append({
                "portfolio_league_id": str(portfolio_league_id),
                "source_league_id": str(source_league_id),
                "season": int(season),
                "week": int(week),
                "league_format": str(league_format),
                "transaction_id": str(tx.get("transaction_id") or ""),
                "created": tx.get("created"),
                "status_updated": tx.get("status_updated"),
                "status": status,
                "player_id": str(pid),
                "roster_id": int(rid) if str(rid).isdigit() else rid,
                "bid": float(bid),
                "budget_cap": float(budget_cap),
                "bid_pct_cap": float(bid) / float(budget_cap) if budget_cap > 0 else None,
                "is_winning_bid": status == "complete",
                "is_failed_claim": status == "failed",
                "is_explicit_competitive_loss": competitive_loss,
                "failure_metadata": tx.get("metadata") if status == "failed" else None,
            })
    return out


def capture_history_for_league(
    league_id: str, league_format: str, target_season: int, target_week: int,
    *, max_seasons: int = 2, fetcher=http_json,
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    errors: list[str] = []
    current_id = str(league_id)
    visited: set[str] = set()
    for depth in range(max(1, int(max_seasons))):
        if not current_id or current_id in visited:
            break
        visited.add(current_id)
        try:
            league = fetcher(f"https://api.sleeper.app/v1/league/{current_id}") or {}
        except Exception as exc:
            errors.append(f"league:{current_id}:{type(exc).__name__}:{exc}")
            break
        season = int(league.get("season") or (target_season - depth))
        settings = league.get("settings") if isinstance(league.get("settings"), dict) else {}
        cap = numeric(settings.get("waiver_budget")) or 100.0
        last_week = int(target_week) if season == int(target_season) else 18
        count_before = len(observations)
        for week in range(1, max(1, last_week) + 1):
            try:
                txs = fetcher(f"https://api.sleeper.app/v1/league/{current_id}/transactions/{week}") or []
                if not isinstance(txs, list):
                    txs = []
            except Exception as exc:
                errors.append(f"transactions:{current_id}:{week}:{type(exc).__name__}:{exc}")
                continue
            observations.extend(normalize_waiver_transactions(
                txs, portfolio_league_id=league_id, source_league_id=current_id,
                season=season, week=week, league_format=league_format, budget_cap=cap,
            ))
        sources.append({
            "source_league_id": current_id,
            "season": season,
            "weeks_requested": last_week,
            "observations": len(observations) - count_before,
            "waiver_budget": cap,
        })
        current_id = str(league.get("previous_league_id") or "").strip()
    observations.sort(key=lambda x: (x["season"], x["week"], x.get("created") or 0, x["transaction_id"], x["player_id"]))
    return {
        "schema": SCHEMA_HISTORY,
        "captured_at": utc_now().isoformat(),
        "portfolio_league_id": str(league_id),
        "league_format": str(league_format),
        "target_season": int(target_season),
        "target_week": int(target_week),
        "max_seasons": int(max_seasons),
        "sources": sources,
        "source_errors": errors,
        "observations": observations,
        "summary": {
            "observations": len(observations),
            "winning_bids": sum(bool(x.get("is_winning_bid")) for x in observations),
            "failed_claims": sum(bool(x.get("is_failed_claim")) for x in observations),
            "explicit_competitive_losses": sum(bool(x.get("is_explicit_competitive_loss")) for x in observations),
        },
    }


def history_before_target(observations: Iterable[dict[str, Any]], season: int, week: int) -> list[dict[str, Any]]:
    """Prospective guard: never use target-week or future-season auction results."""
    out = []
    for row in observations:
        try:
            sy, wk = int(row.get("season")), int(row.get("week"))
        except Exception:
            continue
        if sy < int(season) or (sy == int(season) and wk < int(week)):
            out.append(row)
    return out


def select_bid_sample(
    all_observations: list[dict[str, Any]], *, league_id: str, league_format: str,
    position: str, season: int, week: int,
) -> dict[str, Any]:
    history = history_before_target(all_observations, season, week)
    winners = [x for x in history if bool(x.get("is_winning_bid")) and numeric(x.get("bid_pct_cap")) is not None]
    pos = normalize_position(position)
    scopes = [
        ("LEAGUE_POSITION", [x for x in winners if str(x.get("portfolio_league_id")) == str(league_id) and normalize_position(x.get("position")) == pos], 6),
        ("LEAGUE_ALL", [x for x in winners if str(x.get("portfolio_league_id")) == str(league_id)], 12),
        ("FORMAT_POSITION", [x for x in winners if str(x.get("league_format")) == str(league_format) and normalize_position(x.get("position")) == pos], 12),
        ("FORMAT_ALL", [x for x in winners if str(x.get("league_format")) == str(league_format)], 25),
        ("PORTFOLIO_ALL", winners, 30),
    ]
    for name, sample, minimum in scopes:
        if len(sample) >= minimum:
            return {"scope": name, "sample": sample, "n": len(sample), "minimum": minimum, "sparse": False}
    if len(winners) >= 3:
        return {"scope": "PORTFOLIO_SPARSE", "sample": winners, "n": len(winners), "minimum": 30, "sparse": True}
    return {"scope": "INSUFFICIENT", "sample": winners, "n": len(winners), "minimum": 3, "sparse": True}


def enrich_history_positions(observations: list[dict[str, Any]], current_indexes: dict[str, dict[str, dict[str, Any]]]) -> None:
    """Attach position only when the current governed identity can resolve it.

    Historical bid price remains valid even when an old player is no longer in the
    current identity universe. Such rows simply participate in all-position pools.
    """
    for row in observations:
        if row.get("position"):
            continue
        idx = current_indexes.get(str(row.get("portfolio_league_id"))) or {}
        prow = idx.get(str(row.get("player_id")))
        if prow:
            row["position"] = normalize_position(prow.get("position_model") or prow.get("position"))


def empirical_win_probability(sample: list[dict[str, Any]], bid_pct_cap: float) -> float | None:
    prices = sorted(numeric(x.get("bid_pct_cap")) for x in sample)
    prices = [x for x in prices if x is not None]
    if not prices:
        return None
    wins = sum(x <= bid_pct_cap for x in prices)
    # Laplace smoothing prevents 0/1 certainty from small historical samples.
    return (wins + 1.0) / (len(prices) + 2.0)


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    z = (len(xs) - 1) * q
    lo, hi = int(math.floor(z)), int(math.ceil(z))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - z) + xs[hi] * (z - lo)


def current_row_value(row: dict[str, Any] | None, field: str) -> float | None:
    if not row:
        return None
    if field == "waiver_next3_projection" and not bool(row.get("waiver_activation_eligible")):
        return None
    if field == "decision_weekly_projection" and numeric(row.get(field)) is None:
        return None
    return numeric(row.get(field))


def submitted_week_upgrade(
    candidate: dict[str, Any], roster: dict[str, Any], profile: dict[str, Any], index: dict[str, dict[str, Any]],
) -> tuple[float | None, str | None]:
    c_week = numeric(candidate.get("decision_weekly_projection"))
    c_pos = normalize_position(candidate.get("position_model") or candidate.get("position"))
    if c_week is None or not c_pos:
        return None, None
    starters = valid_ids(roster.get("starters"))
    slots = starter_slots(profile)
    comparisons: list[tuple[float, str]] = []
    for i, pid in enumerate(starters):
        if i >= len(slots) or not position_eligible(slots[i], c_pos):
            continue
        row = index.get(pid)
        val = numeric((row or {}).get("decision_weekly_projection"))
        if val is not None:
            comparisons.append((val, pid))
    if not comparisons:
        return 0.0, None
    weakest, pid = min(comparisons)
    return max(0.0, c_week - weakest), pid


def choose_drop(
    roster: dict[str, Any], index: dict[str, dict[str, Any]], candidate_pid: str,
) -> tuple[dict[str, Any] | None, str | None]:
    starters = set(valid_ids(roster.get("starters")))
    ranked: list[tuple[int, float, str, dict[str, Any]]] = []
    for pid in valid_ids(roster.get("players")):
        if pid == candidate_pid:
            continue
        row = index.get(pid)
        value = current_row_value(row, "waiver_next3_projection")
        if value is None:
            continue
        # Prefer a bench cut when values are comparable. Missing values are never zero-imputed.
        ranked.append((1 if pid in starters else 0, value, pid, row or {}))
    if not ranked:
        return None, None
    ranked.sort(key=lambda x: (x[0], x[1], x[2]))
    _, _, pid, row = ranked[0]
    return row, pid


def weeks_remaining(profile: dict[str, Any], week: int) -> tuple[int, int]:
    settings = profile.get("settings") if isinstance(profile.get("settings"), dict) else {}
    playoff_start = int(numeric(settings.get("playoff_week_start")) or 15)
    regular_end = max(1, playoff_start - 1)
    return max(1, regular_end - int(week) + 1), regular_end


def chopped_supply_context(
    rosters: list[dict[str, Any]], own_roster_id: Any, index: dict[str, dict[str, Any]], free_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    active = [r for r in rosters if valid_ids(r.get("players"))]
    opponent_top: list[float] = []
    covered_rosters = 0
    for roster in active:
        if str(roster.get("roster_id")) == str(own_roster_id):
            continue
        vals = [numeric((index.get(pid) or {}).get("decision_weekly_projection")) for pid in valid_ids(roster.get("players"))]
        vals = sorted([x for x in vals if x is not None], reverse=True)
        if vals:
            covered_rosters += 1
            opponent_top.append(statistics.fmean(vals[: min(3, len(vals))]))
    fa_vals = sorted([numeric(x.get("decision_weekly_projection")) for x in free_candidates], reverse=True)
    fa_vals = [x for x in fa_vals if x is not None]
    current_top = statistics.fmean(fa_vals[: min(5, len(fa_vals))]) if fa_vals else None
    future_top = statistics.fmean(opponent_top) if opponent_top else None
    if current_top is not None and future_top is not None and current_top + future_top > 0:
        supply_index = clamp(future_top / (current_top + future_top), 0.0, 1.0)
    else:
        supply_index = None
    return {
        "teams_remaining_proxy": len(active),
        "opponent_rosters_with_projection_evidence": covered_rosters,
        "current_free_agent_top5_weekly_mean": current_top,
        "expected_eliminated_roster_top3_weekly_mean_proxy": future_top,
        "future_supply_index": supply_index,
        "method": "exchangeability proxy over currently non-empty opponent rosters; not an elimination-probability model",
    }


def competition_adjusted_probability(base: float, opponent_budgets: list[float], bid: float) -> tuple[float, int]:
    if not opponent_budgets:
        return base, 0
    affordable = sum(x >= bid for x in opponent_budgets)
    frac = affordable / len(opponent_budgets)
    adjusted = 1.0 - (1.0 - base) * frac
    return clamp(adjusted, 0.0, 1.0), affordable


def build_bid_curve(
    *, sample: list[dict[str, Any]], budget_cap: float, own_remaining: float, opponent_budgets: list[float],
    player_utility_index: float, preservation_weight: float,
) -> list[dict[str, Any]]:
    curve: list[dict[str, Any]] = []
    max_bid = max(0, int(math.floor(own_remaining)))
    for bid in range(max_bid + 1):
        base = empirical_win_probability(sample, (bid / budget_cap) if budget_cap > 0 else 0.0)
        if base is None:
            continue
        pwin, competitors = competition_adjusted_probability(base, opponent_budgets, float(bid))
        spend_share = (bid / own_remaining) if own_remaining > 0 else 1.0
        cost_index = 100.0 * spend_share * preservation_weight
        eu = pwin * player_utility_index - cost_index
        curve.append({
            "bid": bid,
            "bid_pct_initial_cap": bid / budget_cap if budget_cap > 0 else None,
            "bid_pct_remaining_budget": bid / own_remaining if own_remaining > 0 else None,
            "empirical_base_win_probability": round(base, 6),
            "estimated_win_probability": round(pwin, 6),
            "competitors_able_to_match_or_exceed": competitors,
            "cost_index": round(cost_index, 6),
            "expected_utility_index": round(eu, 6),
        })
    return curve


def candidate_signal(
    candidate: dict[str, Any], own_roster: dict[str, Any], profile: dict[str, Any], index: dict[str, dict[str, Any]],
    *, chopped: bool,
) -> dict[str, Any] | None:
    pid = player_id(candidate)
    if not pid:
        return None
    next3 = current_row_value(candidate, "waiver_next3_projection")
    if next3 is None:
        return None
    drop_row, drop_pid = choose_drop(own_roster, index, pid)
    roster_slots = len(profile.get("roster_positions") or [])
    open_roster_spot = len(valid_ids(own_roster.get("players"))) < roster_slots if roster_slots > 0 else False
    drop_next3 = current_row_value(drop_row, "waiver_next3_projection") if drop_row else None
    if open_roster_spot:
        drop_pid, drop_next3 = None, 0.0
    elif drop_row is None or drop_next3 is None:
        return {
            "player_id": pid,
            "status": "BLOCKED_DROP_VALUE_UNAVAILABLE",
            "candidate_next3_projection": next3,
            "drop_player_id": None,
        }
    next3_delta = next3 - float(drop_next3 or 0.0)
    best_ball = "BESTBALL" in str(profile.get("format") or "").upper()
    if best_ball:
        c_week = numeric(candidate.get("decision_weekly_projection"))
        d_week = numeric((drop_row or {}).get("decision_weekly_projection")) if drop_row else 0.0
        week_delta = max(0.0, float(c_week) - float(d_week)) if c_week is not None and d_week is not None else 0.0
        replace_pid = drop_pid
    else:
        week_delta, replace_pid = submitted_week_upgrade(candidate, own_roster, profile, index)
        week_delta = week_delta if week_delta is not None else 0.0
    p10 = numeric(candidate.get("p10")) if bool(candidate.get("weekly_activation_eligible")) else None
    floor_leverage = 0.0
    if chopped and p10 is not None and replace_pid:
        rp10 = numeric((index.get(replace_pid) or {}).get("p10"))
        if rp10 is not None:
            floor_leverage = max(0.0, p10 - rp10)
    if chopped:
        raw_signal = max(0.0, week_delta) + 0.5 * max(0.0, floor_leverage) + 0.5 * max(0.0, next3_delta)
    else:
        raw_signal = max(0.0, next3_delta) + 0.25 * max(0.0, week_delta)
    return {
        "player_id": pid,
        "status": "READY" if raw_signal > 0 else "NON_POSITIVE_UPGRADE",
        "candidate_next3_projection": next3,
        "drop_player_id": drop_pid,
        "drop_player_name": player_name(drop_row, drop_pid or "") if drop_pid else None,
        "drop_next3_projection": drop_next3,
        "next3_delta": round(next3_delta, 6),
        "submitted_lineup_week_delta": round(week_delta, 6) if not best_ball else None,
        "submitted_lineup_replaced_player_id": replace_pid if not best_ball else None,
        "best_ball_short_term_upgrade_proxy": round(week_delta, 6) if best_ball else None,
        "floor_leverage": round(floor_leverage, 6) if chopped else None,
        "raw_acquisition_signal": round(raw_signal, 6),
    }


def recommendation_from_curve(curve: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not curve:
        return None
    best = max(curve, key=lambda x: (x["expected_utility_index"], -x["bid"]))
    best_eu = float(best["expected_utility_index"])
    tolerance = max(0.5, abs(best_eu) * 0.05)
    near = [x for x in curve if float(x["expected_utility_index"]) >= best_eu - tolerance]
    recommended = int(best["bid"])
    next_row = next((x for x in curve if int(x["bid"]) == recommended + 1), None)
    marginal = None if next_row is None else float(next_row["expected_utility_index"]) - best_eu
    return {
        "recommended_bid": recommended,
        "recommended_bid_range": [min(int(x["bid"]) for x in near), max(int(x["bid"]) for x in near)],
        "estimated_win_probability_at_recommendation": best["estimated_win_probability"],
        "expected_utility_index_at_recommendation": best["expected_utility_index"],
        "marginal_expected_utility_of_plus_1_faab": round(marginal, 6) if marginal is not None else None,
        "likely_competitor_count_at_recommendation": best["competitors_able_to_match_or_exceed"],
    }


def plan_league(
    *, league_id: str, profile: dict[str, Any], current: dict[str, Any], live_league: dict[str, Any],
    rosters: list[dict[str, Any]], users: list[dict[str, Any]], username: str,
    all_history: list[dict[str, Any]], target_season: int, target_week: int,
    max_current_age_hours: float = 36.0, now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    fmt = str(profile.get("format") or current.get("league_format") or "UNKNOWN")
    base = {
        "schema": SCHEMA_LEAGUE,
        "league_id": str(league_id),
        "league_name": live_league.get("name") or profile.get("league_name"),
        "format": fmt,
        "season": int(target_season),
        "week": int(target_week),
        "engine": "CHOPPED" if fmt in CHOPPED_FORMATS else "STANDARD",
        "production_model_unchanged": "M9",
        "research_only": True,
    }
    if str(current.get("league_id") or "") != str(league_id):
        return {**base, "status": "BLOCKED_LEAGUE_ID_MISMATCH"}
    if current.get("profile_current_match") is False:
        return {**base, "status": "BLOCKED_PROFILE_DRIFT", "profile_diff": current.get("profile_diff") or {}}
    if str(current.get("profile_fingerprint") or "") != str(profile.get("profile_fingerprint") or ""):
        return {**base, "status": "BLOCKED_PROFILE_BINDING_MISMATCH"}
    if int(current.get("season") or -1) != int(target_season) or int(current.get("week") or -1) != int(target_week):
        return {**base, "status": "BLOCKED_CURRENT_WEEK_MISMATCH", "current_season": current.get("season"), "current_week": current.get("week")}
    if current.get("target_week_realised_stats_excluded") is not True:
        return {**base, "status": "BLOCKED_TARGET_WEEK_REALIZED_STATS_NOT_EXCLUDED"}
    generated = parse_dt(current.get("generated_at"))
    if generated is None:
        return {**base, "status": "BLOCKED_CURRENT_TIMESTAMP_MISSING"}
    age_h = (now - generated).total_seconds() / 3600.0
    if age_h < -0.25 or age_h > float(max_current_age_hours):
        return {**base, "status": "BLOCKED_STALE_CURRENT", "current_age_hours": round(age_h, 3), "max_current_age_hours": max_current_age_hours}

    live_settings = live_league.get("settings") if isinstance(live_league.get("settings"), dict) else {}
    if int(live_settings.get("disable_adds") or 0) == 1:
        return {**base, "status": "NOT_APPLICABLE_ADDS_DISABLED"}
    cap = numeric(live_settings.get("waiver_budget"))
    if cap is None or cap <= 0:
        return {**base, "status": "NOT_APPLICABLE_NO_FAAB_BUDGET"}

    own, user = managed_roster(rosters, users, username)
    if own is None:
        return {**base, "status": "BLOCKED_MANAGED_ROSTER_UNRESOLVED", "username": username}
    own_remaining = remaining_budget(own, cap)
    if own_remaining <= 0:
        return {**base, "status": "READY_NO_FAAB_REMAINING", "managed_roster_id": own.get("roster_id"), "remaining_faab": 0.0, "recommendations": []}

    index = current_index(current)
    owned_ids = {pid for roster in rosters for pid in valid_ids(roster.get("players"))}
    allowed = rosterable_positions(profile)
    candidates = []
    for row in current.get("players") or []:
        if not isinstance(row, dict) or not bool(row.get("waiver_activation_eligible")):
            continue
        pid = player_id(row)
        pos = normalize_position(row.get("position_model") or row.get("position"))
        if not pid or pid in owned_ids or pos not in allowed or current_row_value(row, "waiver_next3_projection") is None:
            continue
        candidates.append(row)
    if not candidates:
        return {
            **base, "status": "BLOCKED_NO_ELIGIBLE_WAIVER_PROJECTIONS",
            "managed_roster_id": own.get("roster_id"),
            "remaining_faab": own_remaining,
            "current_waiver_activation_eligible": (current.get("summary") or {}).get("waiver_activation_eligible"),
            "source_health_reason": (current.get("source_health") or {}).get("reason"),
        }

    opponent_budgets = [remaining_budget(r, cap) for r in rosters if str(r.get("roster_id")) != str(own.get("roster_id"))]
    chopped = fmt in CHOPPED_FORMATS
    supply = chopped_supply_context(rosters, own.get("roster_id"), index, candidates) if chopped else None
    wrem, regular_end = weeks_remaining(profile, target_week)
    standard_preservation = 0.55 + 0.45 * clamp(wrem / max(1, regular_end), 0.0, 1.0)
    future_supply = numeric((supply or {}).get("future_supply_index")) if chopped else None
    preservation = standard_preservation * (1.0 + 0.8 * (future_supply if future_supply is not None else 0.5)) if chopped else standard_preservation

    signals = []
    blocked_candidates = []
    for row in candidates:
        sig = candidate_signal(row, own, profile, index, chopped=chopped)
        if not sig:
            continue
        if sig.get("status") == "BLOCKED_DROP_VALUE_UNAVAILABLE":
            blocked_candidates.append(sig)
        elif sig.get("status") == "READY":
            signals.append((row, sig))
    if not signals:
        return {
            **base, "status": "BLOCKED_NO_POSITIVE_ADD_DROP_UPGRADES",
            "managed_roster_id": own.get("roster_id"), "remaining_faab": own_remaining,
            "blocked_candidate_count": len(blocked_candidates),
        }

    max_signal = max(float(sig["raw_acquisition_signal"]) for _, sig in signals)
    recommendations = []
    history_counts = Counter()
    for row, sig in sorted(signals, key=lambda x: float(x[1]["raw_acquisition_signal"]), reverse=True)[:30]:
        pid = str(sig["player_id"])
        pos = normalize_position(row.get("position_model") or row.get("position"))
        sample_info = select_bid_sample(all_history, league_id=league_id, league_format=fmt, position=pos, season=target_season, week=target_week)
        history_counts[sample_info["scope"]] += 1
        utility = 100.0 * float(sig["raw_acquisition_signal"]) / max_signal if max_signal > 0 else 0.0
        if chopped:
            teams_now = max(1, int((supply or {}).get("teams_remaining_proxy") or len(rosters) or 1))
            teams_initial = max(teams_now, int(profile.get("total_rosters") or teams_now))
            survival_multiplier = 1.0 + 0.7 * (1.0 - teams_now / teams_initial)
            utility *= survival_multiplier
        else:
            survival_multiplier = 1.0
        sample = sample_info["sample"]
        curve = build_bid_curve(
            sample=sample, budget_cap=cap, own_remaining=own_remaining, opponent_budgets=opponent_budgets,
            player_utility_index=utility, preservation_weight=preservation,
        ) if len(sample) >= 3 else []
        rec = recommendation_from_curve(curve)
        prices = [numeric(x.get("bid_pct_cap")) for x in sample]
        prices = [x for x in prices if x is not None]
        hist_before = history_before_target(all_history, target_season, target_week)
        explicit_losses = sum(
            bool(x.get("is_explicit_competitive_loss"))
            for x in hist_before
            if str(x.get("portfolio_league_id")) == str(league_id)
        )
        confidence_score = clamp(20 + min(50, sample_info["n"] * 2.0) + min(15, explicit_losses * 1.5) + (10 if bool(row.get("waiver_activation_eligible")) else 0), 0, 95)
        confidence = "HIGH" if confidence_score >= 75 else "MEDIUM" if confidence_score >= 50 else "LOW"
        status = "READY_EMPIRICAL_BIDS" if rec and not sample_info["sparse"] else "PARTIAL_SPARSE_BID_HISTORY" if rec else "BLOCKED_INSUFFICIENT_BID_HISTORY"
        recommendations.append({
            "player_id": pid,
            "player_name": player_name(row, pid),
            "position": pos,
            "team": row.get("team"),
            "status": status,
            "projection_evidence": {
                "waiver_next3_projection": current_row_value(row, "waiver_next3_projection"),
                "decision_weekly_projection": numeric(row.get("decision_weekly_projection")),
                "p10": numeric(row.get("p10")) if bool(row.get("weekly_activation_eligible")) else None,
                "waiver_feature_coverage": numeric(row.get("waiver_feature_coverage")),
                "projection_source": row.get("projection_source"),
            },
            "add_drop": sig,
            "player_utility_index": round(utility, 6),
            "survival_multiplier": round(survival_multiplier, 6) if chopped else None,
            "budget_preservation_weight": round(preservation, 6),
            "bid_history": {
                "scope": sample_info["scope"],
                "winning_bid_sample_n": sample_info["n"],
                "sparse": sample_info["sparse"],
                "winning_bid_pct_cap_p50": quantile(prices, 0.50),
                "winning_bid_pct_cap_p75": quantile(prices, 0.75),
                "winning_bid_pct_cap_p90": quantile(prices, 0.90),
                "explicit_competitive_losses_in_league_history": explicit_losses,
                "target_week_results_excluded": True,
            },
            "recommendation": rec,
            "win_probability_curve": curve,
            "confidence": confidence,
            "confidence_score": round(confidence_score, 3),
            "valuation_horizon": "SHORT_HORIZON_ONLY" if "DYNASTY" in fmt else "IN_SEASON",
            "rationale": [
                "Uses governed FIE waiver-next-3 evidence; missing values are not zero-imputed.",
                "Win probability is empirical from observable winning bids, adjusted only for current competitor affordability.",
                "Target-week auction outcomes are excluded from the recommendation sample.",
                "Chopped utility separately accounts for immediate survival leverage and expected future chopped-roster supply." if chopped else "Standard utility emphasizes short-horizon roster upgrade and budget preservation across remaining weeks.",
            ],
        })

    def _rec_sort(row: dict[str, Any]) -> tuple[float, float, str]:
        rec = row.get("recommendation") or {}
        eu = numeric(rec.get("expected_utility_index_at_recommendation"))
        return (-(eu if eu is not None else -1e9), -float(row.get("player_utility_index") or 0), str(row.get("player_name") or ""))
    recommendations.sort(key=_rec_sort)
    ready_count = sum(x.get("recommendation") is not None for x in recommendations)
    overall_status = "READY" if ready_count else "BLOCKED_INSUFFICIENT_BID_HISTORY"
    if ready_count and any(x.get("status") == "PARTIAL_SPARSE_BID_HISTORY" for x in recommendations):
        overall_status = "PARTIAL_SPARSE_BID_HISTORY"
    return {
        **base,
        "status": overall_status,
        "managed_user_id": (user or {}).get("user_id"),
        "managed_roster_id": own.get("roster_id"),
        "faab": {
            "initial_budget": cap,
            "remaining_budget": own_remaining,
            "opponent_remaining_budgets": opponent_budgets,
            "opponent_budget_p50": quantile(opponent_budgets, 0.5),
            "opponent_budget_max": max(opponent_budgets) if opponent_budgets else None,
        },
        "timing": {"weeks_remaining": wrem, "regular_season_end_week": regular_end},
        "chopped_context": supply,
        "candidate_count": len(candidates),
        "positive_upgrade_count": len(signals),
        "blocked_drop_value_candidates": len(blocked_candidates),
        "recommendation_count": ready_count,
        "history_scope_usage": dict(history_counts),
        "recommendations": recommendations,
        "governance": {
            "research_only": True,
            "production_model": "M9",
            "canonical_rankings_changed": False,
            "adp_used_as_football_feature": False,
            "target_week_waiver_results_used": False,
            "hidden_losing_bids_invented": False,
            "no_bid_behavior_invented": False,
        },
    }


def _portfolio_entries(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for row in config.get("leagues") or []:
        if isinstance(row, dict) and row.get("league_id"):
            out[str(row["league_id"])] = row
    return out


def _enabled_registry(registry: dict[str, Any]) -> list[str]:
    return [
        str(lid) for lid, row in sorted((registry.get("leagues") or {}).items())
        if isinstance(row, dict) and row.get("enabled", True)
    ]


def live_profile_matches(profile: dict[str, Any], live_league: dict[str, Any], portfolio_entry: dict[str, Any] | None) -> tuple[bool, str | None]:
    try:
        from league_profile import build_profile  # type: ignore
        rebuilt = build_profile(
            str(profile.get("league_id")),
            str(profile.get("format") or "AUTO"),
            league_json=live_league,
            portfolio_entry=portfolio_entry,
        )
        actual = str(rebuilt.get("profile_fingerprint") or "")
        expected = str(profile.get("profile_fingerprint") or "")
        return bool(actual and expected and actual == expected), actual
    except Exception:
        # Current snapshot still carries its own live-profile gate. If we cannot
        # independently restamp here, do not claim a live match.
        return False, None


def markdown_portfolio(report: dict[str, Any]) -> str:
    lines = [
        f"# FIE Window 1D Waiver Plan · Week {report.get('week')}", "",
        f"Generated: `{report.get('generated_at')}`", "",
        "Research-only decision support. M9 production and canonical rankings are unchanged.", "",
        "## Portfolio status", "",
    ]
    for league in report.get("leagues") or []:
        lines.append(f"### {league.get('league_name') or league.get('league_id')} · {league.get('format')} · {league.get('status')}")
        if league.get("status", "").startswith("BLOCKED") or league.get("status", "").startswith("NOT_APPLICABLE"):
            lines.extend(["", f"No bid recommendation produced. Reason: `{league.get('status')}`", ""])
            continue
        faab = league.get("faab") or {}
        lines.extend(["", f"FAAB remaining: **{faab.get('remaining_budget')} / {faab.get('initial_budget')}**", ""])
        if league.get("engine") == "CHOPPED":
            c = league.get("chopped_context") or {}
            lines.append(f"Chopped context: teams remaining proxy **{c.get('teams_remaining_proxy')}**, future supply index **{c.get('future_supply_index')}**.")
            lines.append("")
        rows = [x for x in (league.get("recommendations") or []) if x.get("recommendation")][:10]
        if not rows:
            lines.extend(["No empirical bid recommendation is currently available.", ""])
            continue
        lines.extend(["| Player | Pos | Add→Drop signal | Bid | Range | Win P | Confidence |", "|---|---:|---:|---:|---:|---:|---|"])
        for row in rows:
            rec = row.get("recommendation") or {}
            sig = row.get("add_drop") or {}
            rng = rec.get("recommended_bid_range") or [None, None]
            lines.append(
                f"| {row.get('player_name')} | {row.get('position')} | {sig.get('raw_acquisition_signal')} | "
                f"{rec.get('recommended_bid')} | {rng[0]}–{rng[1]} | {rec.get('estimated_win_probability_at_recommendation')} | {row.get('confidence')} |"
            )
        lines.append("")
    lines.extend([
        "## Interpretation", "",
        "Winning-price curves use only Sleeper waiver bids that are explicitly observable. Failed claims are not assumed to be competitive losses unless Sleeper metadata says so. Invisible/no-bid behavior is never fabricated.", "",
        "For Chopped leagues, the optimizer uses a separate preservation policy that values immediate survival leverage against the expected quality of future eliminated-roster supply. The future-supply component is a transparent exchangeability proxy, not a calibrated elimination model.", "",
    ])
    return "\n".join(lines)


def build_portfolio(
    *, root: Path, season: int, week: int | None, league_id: str | None,
    max_history_seasons: int, max_current_age_hours: float, fetcher=http_json,
) -> dict[str, Any]:
    registry = read_json(root / "data/research/leagues/registry.json", {}) or {}
    portfolio = read_json(root / "config/league-portfolio.json", {}) or {}
    entries = _portfolio_entries(portfolio)
    username = str(portfolio.get("sleeper_username") or "")
    if not username:
        raise EvidenceError("PORTFOLIO_SLEEPER_USERNAME_MISSING")
    if week is None:
        state = fetcher("https://api.sleeper.app/v1/state/nfl") or {}
        week = int(state.get("week") or state.get("leg") or 1)
        if str(state.get("season_type") or "").lower() in {"pre", "preseason"}:
            week = 1
    target_week = int(week)
    ids = [str(league_id)] if league_id else _enabled_registry(registry)

    live_state: dict[str, tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]] = {}
    currents: dict[str, dict[str, Any]] = {}
    histories: dict[str, dict[str, Any]] = {}
    all_observations: list[dict[str, Any]] = []
    current_indexes: dict[str, dict[str, dict[str, Any]]] = {}
    preblocks: dict[str, dict[str, Any]] = {}

    for lid in ids:
        profile = read_json(root / f"data/research/leagues/{lid}/profile.json", {}) or {}
        current_path = root / f"data/research/leagues/{lid}/current/milestone5_current.json"
        try:
            current = load_current(current_path, root=root)
            currents[lid] = current
            current_indexes[lid] = current_index(current)
        except Exception as exc:
            preblocks[lid] = {"status": "BLOCKED_CURRENT_LOAD", "detail": f"{type(exc).__name__}:{exc}"}
            continue
        try:
            live_league = fetcher(f"https://api.sleeper.app/v1/league/{lid}") or {}
            rosters = fetcher(f"https://api.sleeper.app/v1/league/{lid}/rosters") or []
            users = fetcher(f"https://api.sleeper.app/v1/league/{lid}/users") or []
            live_state[lid] = (live_league, rosters if isinstance(rosters, list) else [], users if isinstance(users, list) else [])
        except Exception as exc:
            preblocks[lid] = {"status": "BLOCKED_LIVE_SLEEPER_STATE", "detail": f"{type(exc).__name__}:{exc}"}
            continue
        match, live_fp = live_profile_matches(profile, live_league, entries.get(lid))
        if not match:
            preblocks[lid] = {"status": "BLOCKED_PROFILE_DRIFT", "stored_profile_fingerprint": profile.get("profile_fingerprint"), "live_profile_fingerprint": live_fp}
            continue
        hist = capture_history_for_league(
            lid, str(profile.get("format") or "UNKNOWN"), int(season), target_week,
            max_seasons=max_history_seasons, fetcher=fetcher,
        )
        histories[lid] = hist
        all_observations.extend(hist.get("observations") or [])

    enrich_history_positions(all_observations, current_indexes)
    leagues = []
    source_bindings = {}
    for lid in ids:
        profile_path = root / f"data/research/leagues/{lid}/profile.json"
        current_path = root / f"data/research/leagues/{lid}/current/milestone5_current.json"
        profile = read_json(profile_path, {}) or {}
        if lid in preblocks:
            leagues.append({
                "schema": SCHEMA_LEAGUE, "league_id": lid, "league_name": profile.get("league_name"),
                "format": profile.get("format"), "season": season, "week": target_week,
                "engine": "CHOPPED" if str(profile.get("format")) in CHOPPED_FORMATS else "STANDARD",
                **preblocks[lid], "research_only": True, "production_model_unchanged": "M9",
            })
            continue
        live_league, rosters, users = live_state[lid]
        plan = plan_league(
            league_id=lid, profile=profile, current=currents[lid], live_league=live_league,
            rosters=rosters, users=users, username=username, all_history=all_observations,
            target_season=season, target_week=target_week, max_current_age_hours=max_current_age_hours,
        )
        hist = histories.get(lid) or {}
        plan["source_bindings"] = {
            "profile_sha256": sha256_file(profile_path) if profile_path.is_file() else None,
            "current_snapshot_sha256": sha256_file(current_path) if current_path.is_file() else None,
            "live_state_sha256": sha256_json({"league": live_league, "rosters": rosters, "users": users}),
            "waiver_history_sha256": sha256_json(hist),
        }
        leagues.append(plan)
        source_bindings[lid] = plan["source_bindings"]

    counts = Counter(str(x.get("status")) for x in leagues)
    generated = utc_now()
    capture_id = generated.strftime("%Y%m%dT%H%M%SZ")
    return {
        "schema": SCHEMA_PORTFOLIO,
        "generated_at": generated.isoformat(),
        "capture_id": capture_id,
        "season": int(season),
        "week": target_week,
        "managed_username": username,
        "enabled_league_count": len(ids),
        "league_count": len(leagues),
        "status_counts": dict(counts),
        "leagues": leagues,
        "history": {
            "portfolio_observation_count": len(all_observations),
            "winning_bid_count": sum(bool(x.get("is_winning_bid")) for x in all_observations),
            "failed_claim_count": sum(bool(x.get("is_failed_claim")) for x in all_observations),
            "explicit_competitive_loss_count": sum(bool(x.get("is_explicit_competitive_loss")) for x in all_observations),
            "target_week_results_excluded_from_models": True,
            "max_seasons_per_league": max_history_seasons,
        },
        "source_bindings": source_bindings,
        "governance": {
            "research_only": True,
            "production_model": "M9",
            "production_activation_changed": False,
            "canonical_rankings_changed": False,
            "adp_used_as_football_feature": False,
            "hidden_bids_invented": False,
            "target_week_outcome_leakage_allowed": False,
        },
        "_history_artifacts": histories,
    }


def write_portfolio_outputs(root: Path, report: dict[str, Any]) -> list[Path]:
    season, week = int(report["season"]), int(report["week"])
    capture_id = str(report["capture_id"])
    histories = report.pop("_history_artifacts", {})
    written: list[Path] = []
    history_root = root / f"data/research/evaluation/{season}/waivers/history"
    for lid, hist in histories.items():
        p = history_root / f"league-{lid}.json"
        write_json(p, hist)
        written.append(p)
    out_root = root / f"data/research/evaluation/{season}/weeks/week-{week}/waivers"
    latest_json = out_root / "portfolio-latest.json"
    latest_md = out_root / "portfolio-latest.md"
    capture_json = out_root / "captures" / f"portfolio-{capture_id}.json"
    write_json(latest_json, report)
    write_json(capture_json, report)
    latest_md.parent.mkdir(parents=True, exist_ok=True)
    latest_md.write_text(markdown_portfolio(report) + "\n", encoding="utf-8")
    written.extend([latest_json, capture_json, latest_md])
    return written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="FIE Window 1D optimal waiver / Chopped engine")
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("portfolio")
    b.add_argument("--season", type=int, default=2026)
    b.add_argument("--week", type=int, default=None)
    b.add_argument("--league-id", default="")
    b.add_argument("--max-history-seasons", type=int, default=2)
    b.add_argument("--max-current-age-hours", type=float, default=36.0)
    b.add_argument("--root", default=str(ROOT))
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "portfolio":
        root = Path(args.root).resolve()
        report = build_portfolio(
            root=root, season=int(args.season), week=args.week,
            league_id=str(args.league_id).strip() or None,
            max_history_seasons=int(args.max_history_seasons),
            max_current_age_hours=float(args.max_current_age_hours),
        )
        paths = write_portfolio_outputs(root, report)
        print(f"Window 1D portfolio week={report['week']} leagues={report['league_count']} observations={report['history']['portfolio_observation_count']}")
        for p in paths:
            print(p.relative_to(root))
        return 0
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
