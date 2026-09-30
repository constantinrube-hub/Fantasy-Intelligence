#!/usr/bin/env python3
"""Build a typed, immutable outcome envelope for one PR2 lineup capture.

Input stats are deliberately explicit and identity-keyed.  A provider adapter
may create that raw envelope later, but this scorer never requests a provider
or substitutes a later current snapshot for the captured roster universe.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from point_in_time_capture import build_envelope, first_write_json, sha256_bytes, canonical_bytes
    from weekly_lineup_decision_support import numeric
except ModuleNotFoundError:  # pragma: no cover - package import support
    from research.point_in_time_capture import build_envelope, first_write_json, sha256_bytes, canonical_bytes
    from research.weekly_lineup_decision_support import numeric


ROOT = Path(__file__).resolve().parents[1]
RAW_SCHEMA = "fie-in-season-pr2-lineup-raw-outcome-stats-v1"
OUTCOME_SCHEMA = "fie-in-season-pr2-lineup-outcome-v1"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


FIELD_ALIASES = {
    "pass_yd": ["passing_yards", "pass_yd"], "pass_td": ["passing_tds", "pass_td"], "pass_int": ["passing_interceptions", "pass_int", "interceptions"], "pass_cmp": ["completions", "pass_cmp"], "pass_att": ["attempts", "passing_attempts", "pass_att"], "pass_2pt": ["passing_2pt_conversions", "pass_2pt"], "pass_fd": ["passing_first_downs", "pass_fd"],
    "rush_yd": ["rushing_yards", "rush_yd"], "rush_td": ["rushing_tds", "rush_td"], "rush_att": ["carries", "rushing_attempts", "rush_att"], "rush_2pt": ["rushing_2pt_conversions", "rush_2pt"], "rush_fd": ["rushing_first_downs", "rush_fd"],
    "rec": ["receptions", "rec"], "rec_yd": ["receiving_yards", "rec_yd"], "rec_td": ["receiving_tds", "rec_td"], "rec_tgt": ["targets", "rec_tgt"], "rec_2pt": ["receiving_2pt_conversions", "rec_2pt"], "rec_fd": ["receiving_first_downs", "rec_fd"],
    "fum_lost": ["fumbles_lost", "fum_lost"], "tkl_solo": ["tackles_solo", "def_tackles_solo", "tkl_solo"], "tkl_ast": ["tackles_with_assist", "tackles_assists", "def_tackles_assist", "tkl_ast"], "tkl_loss": ["tackles_for_loss", "def_tackles_for_loss", "tkl_loss"], "sack": ["def_sacks", "sacks", "sack"], "qb_hit": ["def_qb_hits", "qb_hits", "qb_hit"], "int": ["def_interceptions", "interceptions_defense", "int"], "pass_def": ["def_pass_defended", "passes_defended", "pass_def"], "ff": ["def_fumbles_forced", "fumbles_forced", "ff"], "fum_rec": ["def_fumbles", "fumble_recoveries", "fum_rec"], "def_td": ["def_tds", "defensive_tds", "def_td"],
}
BONUS = {"bonus_pass_yd_300": ("pass_yd", 300), "bonus_pass_yd_400": ("pass_yd", 400), "bonus_rush_yd_100": ("rush_yd", 100), "bonus_rush_yd_200": ("rush_yd", 200), "bonus_rec_yd_100": ("rec_yd", 100), "bonus_rec_yd_200": ("rec_yd", 200)}
NORMALIZED_FIELDS = sorted({field for aliases in FIELD_ALIASES.values() for field in aliases})


def normalized_stats(raw: dict[str, Any], *, sparse_zero_is_explicit: bool) -> dict[str, Any]:
    if not sparse_zero_is_explicit:
        raise ValueError("raw outcome source must explicitly declare sparse zero-field semantics")
    row = {field: 0.0 for field in NORMALIZED_FIELDS}
    row.update({str(key): value for key, value in raw.items()})
    return row


def _value(raw: dict[str, Any], key: str) -> float:
    for field in FIELD_ALIASES.get(key, [key]):
        value = numeric(raw.get(field))
        if value is not None:
            return value
    return 0.0


def _bucket(key: str, value: float) -> float:
    token = key.rsplit("_", 1)[-1]
    if token == "0":
        return float(value == 0)
    if token.endswith("p"):
        return float(value >= float(token[:-1]))
    match = re.search(r"_(\d+)_(\d+)$", key)
    return float(bool(match and float(match.group(1)) <= value <= float(match.group(2))))


def _relevant(key: str, position: str) -> bool:
    k = key.lower(); p = position.upper()
    if p == "K": return k.startswith("fg") or k in {"xpm", "xpmiss"}
    if p in {"DEF", "DST", "D/ST"}: return k.startswith(("def_", "pts_allow_", "yds_allow_")) or k in {"sack", "int", "ff", "fum_rec", "safe", "blk_kick"}
    if p in {"DL", "LB", "DB"}: return k in {"tkl_solo", "tkl_ast", "tkl_loss", "sack", "qb_hit", "int", "pass_def", "ff", "fum_rec", "def_td"}
    if p == "QB": return k.startswith("pass_") or k.startswith("rush_") or k == "fum_lost"
    if p in {"RB", "WR", "TE"}: return k.startswith(("rush_", "rec_")) or k in {"rec", "fum_lost"}
    return False


def _special_value(raw: dict[str, Any], key: str) -> float | None:
    k = key.lower()
    if k.startswith("pts_allow_"):
        value = numeric(raw.get("points_allowed", raw.get("pts_allow")))
        return _bucket(k, value) if value is not None else None
    if k.startswith("yds_allow_"):
        value = numeric(raw.get("yards_allowed", raw.get("yds_allow")))
        return _bucket(k, value) if value is not None else None
    value = numeric(raw.get(k))
    return value


def score_candidate(candidate: dict[str, Any], raw: dict[str, Any], scoring: dict[str, Any], *, sparse_zero_is_explicit: bool) -> tuple[float | None, dict[str, Any]]:
    position = str(candidate.get("position_model") or "").upper()
    row = normalized_stats(raw, sparse_zero_is_explicit=sparse_zero_is_explicit)
    points, unsupported = 0.0, []
    for key, weight in (scoring or {}).items():
        number = numeric(weight)
        if number is None or number == 0 or not _relevant(str(key), position):
            continue
        k = str(key).lower()
        if k in BONUS:
            source, threshold = BONUS[k]
            value = _value(row, source)
            points += float(value >= threshold) * number
        elif k in {"bonus_rec_te", "rec_te", "bonus_rec_rb", "rec_rb", "bonus_rec_wr", "rec_wr"}:
            target = "TE" if k.endswith("te") else ("RB" if k.endswith("rb") else "WR")
            if position == target:
                points += _value(row, "rec") * number
        elif position in {"K", "DEF", "DST", "D/ST"}:
            value = _special_value(row, k)
            if value is None:
                unsupported.append(k)
            else:
                points += value * number
        elif k in FIELD_ALIASES:
            points += _value(row, k) * number
        else:
            unsupported.append(k)
    return (None if unsupported else float(points), {"position": position, "exact": not unsupported, "unsupported": sorted(unsupported)})


def build_outcome(capture: dict[str, Any], raw: dict[str, Any], *, outcome_revision_id: str) -> dict[str, Any]:
    if raw.get("schema") != RAW_SCHEMA:
        raise ValueError("raw outcome stats schema invalid")
    if not capture.get("capture_id") or not capture.get("capture_content_sha256"):
        raise ValueError("immutable capture required")
    stats = raw.get("stats_by_player_id") if isinstance(raw.get("stats_by_player_id"), dict) else {}
    sparse_zero_is_explicit = raw.get("sparse_zero_fields_are_explicit") is True
    values, replay = {}, {}
    for report in capture.get("leagues") or []:
        if not isinstance(report, dict) or report.get("status") == "NOT_APPLICABLE_AUTOMATIC_LINEUP":
            continue
        source = report.get("evaluation_input") or {}
        league_id = str(report.get("league_id") or "")
        scoring = source.get("scoring_settings") if isinstance(source.get("scoring_settings"), dict) else {}
        if source.get("schema") != "fie-in-season-pr2-lineup-evaluation-input-v1" or not scoring:
            replay[league_id] = {"status": "BLOCKED_CAPTURE_SCORING_INPUT_MISSING"}
            continue
        league_values, blockers = {}, []
        for candidate in source.get("active_candidates") or []:
            if not isinstance(candidate, dict):
                continue
            player_id = str(candidate.get("captured_player_id") or "")
            raw_row = stats.get(player_id)
            if not isinstance(raw_row, dict):
                blockers.append({"player_id": player_id, "code": "RAW_PLAYER_STAT_MISSING"})
                continue
            points, diagnostic = score_candidate(candidate, raw_row, scoring, sparse_zero_is_explicit=sparse_zero_is_explicit)
            if points is None:
                blockers.append({"player_id": player_id, "code": "SCORING_REPLAY_NOT_EXACT", "detail": diagnostic})
                continue
            league_values[player_id] = round(points, 6)
        if blockers:
            replay[league_id] = {"status": "BLOCKED_OUTCOME_REPLAY_INCOMPLETE", "blockers": blockers}
        else:
            values[league_id] = dict(sorted(league_values.items()))
            replay[league_id] = {"status": "READY", "player_count": len(league_values), "scoring_signature": (report.get("evidence") or {}).get("scoring_signature")}
    return {
        "schema": OUTCOME_SCHEMA,
        "capture_id": capture["capture_id"],
        "capture_content_sha256": capture["capture_content_sha256"],
        "outcome_revision_id": str(outcome_revision_id),
        "season": capture.get("leagues", [{}])[0].get("season") if capture.get("leagues") else None,
        "week": capture.get("leagues", [{}])[0].get("week") if capture.get("leagues") else None,
        "outcome_observed_at": raw.get("observed_at"),
        "raw_outcome_payload_sha256": sha256_bytes(canonical_bytes(raw)),
        "league_player_realized_points": values,
        "league_scoring_replay": replay,
        "governance": {"research_only": True, "production_model": "M9", "missing_outcomes_zero_imputed": False, "raw_stats_provider_adapter": False},
    }


def write_outcome(output_dir: Path, outcome: dict[str, Any], raw: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = build_envelope(
        capture_id=f"{outcome['capture_id']}-{outcome['outcome_revision_id']}",
        capture_intent="OTHER_GOVERNED",
        provider=str(raw.get("provider") or "explicit-outcome-input"),
        endpoint=str(raw.get("endpoint") or "explicit identity-keyed raw outcome input"),
        observed_at=str(raw.get("observed_at")),
        as_of_semantics="Raw outcome observations are scored only against the immutable capture-bound candidate universe.",
        payload=raw,
        revision_metadata_status="UNKNOWN",
    )
    source_path, outcome_path = output_dir / "source-envelope.json", output_dir / "outcome.json"
    first_write_json(source_path, source)
    first_write_json(outcome_path, outcome)
    return {"source": source_path, "outcome": outcome_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score explicit raw outcomes for one immutable PR2 lineup capture")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--raw-stats", required=True)
    parser.add_argument("--outcome-revision-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    capture, raw = read_json(Path(args.capture)), read_json(Path(args.raw_stats))
    outcome = build_outcome(capture, raw, outcome_revision_id=args.outcome_revision_id)
    paths = write_outcome(Path(args.output_dir), outcome, raw)
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
