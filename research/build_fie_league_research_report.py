#!/usr/bin/env python3
"""Build deterministic per-league FIE research reports from the canonical board.

No model or rank is calculated here.  The report groups and filters the final
league board produced by ``build_fie_final_league_board.py`` and exposes compact
JSON for the app plus auditable Markdown for humans.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from fie_research_pipeline_contract import (
    REPORT_SCHEMA, load_json, load_profile, pipeline_dir, profile_format,
    roster_positions, scoring_settings, team_count, write_json,
)

TOP_N = {"QB": 10, "RB": 20, "WR": 20, "TE": 10, "DST": 10, "K": 10}
SLEEPER_N = {"QB": 10, "RB": 15, "WR": 15, "TE": 10}


def finite(v: Any) -> float | None:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def truth(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes"}


def _row(row: dict) -> dict:
    keys = (
        "player_id", "sleeper_id", "name", "team", "position", "projection_scope",
        "model_selected", "model_status", "projection_points", "projection_ppg",
        "p10", "p25", "p50", "p75", "p90", "position_rank", "overall_rank",
        "replacement_points", "vorp", "adp", "adp_key", "market_position_rank",
        "market_overall_rank", "rank_edge_position", "rank_edge_overall",
        "value_label", "actionable_signal", "confidence", "current_active",
        "injury_status", "draft_relevant", "within_draft_horizon",
        "within_watchlist_horizon", "adp_change_7d", "reason_codes",
        "research_challenger_model", "research_challenger_projection",
        "research_challenger_delta", "research_challenger_status",
    )
    out = {k: row.get(k) for k in keys}
    for k in (
        "projection_points", "projection_ppg", "p10", "p25", "p50", "p75", "p90",
        "position_rank", "overall_rank", "replacement_points", "vorp", "adp",
        "market_position_rank", "market_overall_rank", "rank_edge_position",
        "rank_edge_overall", "confidence", "adp_change_7d",
        "research_challenger_projection", "research_challenger_delta",
    ):
        out[k] = finite(out.get(k))
    for k in ("actionable_signal", "current_active", "draft_relevant", "within_draft_horizon", "within_watchlist_horizon"):
        out[k] = truth(out.get(k))
    rc = out.get("reason_codes")
    if isinstance(rc, str):
        try:
            rc = json.loads(rc)
        except Exception:
            rc = [x for x in rc.split("|") if x]
    out["reason_codes"] = rc if isinstance(rc, list) else []
    return out


def _valid_player(row: dict) -> bool:
    return bool(str(row.get("name") or "").strip() and (row.get("player_id") or row.get("sleeper_id")))


def _top(rows: list[dict], pos: str) -> list[dict]:
    q = [r for r in rows if r.get("position") == pos and _valid_player(r) and r.get("projection_points") is not None]
    q.sort(key=lambda r: (
        r.get("position_rank") is None,
        r.get("position_rank") if r.get("position_rank") is not None else 99999,
        -(r.get("projection_points") or -1e9),
        str(r.get("name") or ""),
    ))
    return q[: TOP_N[pos]]


def _top100_outliers(rows: list[dict]) -> dict:
    universe = [
        r for r in rows if r.get("position") in {"QB", "RB", "WR", "TE"}
        and r.get("adp") is not None and 0 < r["adp"] <= 100
        and r.get("projection_points") is not None and r.get("rank_edge_position") is not None
        and r.get("current_active")
    ]
    pos, neg = [], []
    for r in universe:
        edge = r["rank_edge_position"]
        vorp = r.get("vorp")
        label = str(r.get("value_label") or "")
        if ((edge >= 8) or label in {"VALUE", "STRONG_VALUE"}) and vorp is not None and vorp >= 0:
            x = dict(r); x["outlier_strength"] = "STRONG" if edge >= 18 else "VALUE"; pos.append(x)
        if edge <= -8 or label in {"OVERPRICED", "STRONG_FADE"}:
            x = dict(r); x["outlier_strength"] = "STRONG" if edge <= -18 else "FADE"; neg.append(x)
    pos.sort(key=lambda r: (-abs(r["rank_edge_position"]), -(r.get("vorp") or -1e9), str(r.get("name") or "")))
    neg.sort(key=lambda r: (-abs(r["rank_edge_position"]), r.get("vorp") if r.get("vorp") is not None else 1e9, str(r.get("name") or "")))
    return {"positive": pos, "negative": neg}


def _sleeper_reasons(r: dict, profile: dict) -> list[str]:
    codes = ["LEAGUE_SPECIFIC_VORP", "RELEVANT_UNIVERSE_RANK_EDGE", "M9_PRODUCTION_MODEL", "CURRENT_PLAYER_MATCH"]
    slots = roster_positions(profile)
    if "FLEX" in slots or any(s in {"WRT", "REC_FLEX"} for s in slots):
        codes.append("FLEX_SCARCITY")
    if any(s in {"SUPER_FLEX", "SUPERFLEX", "SF"} for s in slots) or slots.count("QB") >= 2:
        codes.append("SUPERFLEX_SCARCITY")
    if (r.get("adp_change_7d") or 0) > 0:
        codes.append("POSITIVE_MARKET_MOVEMENT")
    return codes


def _sleepers(rows: list[dict], profile: dict) -> dict:
    out: dict[str, list[dict]] = {}
    for pos in ("QB", "RB", "WR", "TE"):
        q = []
        for r in rows:
            if r.get("position") != pos or not _valid_player(r):
                continue
            adp, edge, vorp = r.get("adp"), r.get("rank_edge_position"), r.get("vorp")
            if adp is None or adp <= 100 or edge is None or edge < 8 or vorp is None or vorp < 0:
                continue
            if not r.get("within_watchlist_horizon") or not r.get("current_active"):
                continue
            x = dict(r)
            x["sleeper_strength"] = "STRONG" if edge >= 18 else "VALUE"
            x["why"] = _sleeper_reasons(r, profile)
            q.append(x)
        q.sort(key=lambda r: (-r["rank_edge_position"], -(r.get("vorp") or -1e9), r.get("adp") or 1e9, str(r.get("name") or "")))
        out[pos] = q[: SLEEPER_N[pos]]
    return out


def _score_overview(profile: dict) -> dict:
    scoring = scoring_settings(profile)
    bonuses = {k: v for k, v in scoring.items() if "bonus" in str(k).lower() and finite(v) not in (None, 0)}
    return {
        "receptions": finite(scoring.get("rec")) or 0.0,
        "ppr_label": "PPR" if (finite(scoring.get("rec")) or 0) >= .75 else ("HALF_PPR" if (finite(scoring.get("rec")) or 0) >= .25 else "STANDARD"),
        "pass_td": finite(scoring.get("pass_td")),
        "pass_int": finite(scoring.get("pass_int")),
        "fumble": finite(scoring.get("fum")),
        "fumble_lost": finite(scoring.get("fum_lost")),
        "bonuses": bonuses,
    }


def build_report(league_id: str, season: int, readiness: dict, board: pd.DataFrame) -> tuple[dict, dict, str]:
    profile = load_profile(league_id)
    rows = [_row(r) for r in board.to_dict("records")]
    positions = readiness.get("positions") or {}
    top = {pos: _top(rows, pos) for pos in TOP_N}
    outliers = _top100_outliers(rows)
    sleepers = _sleepers(rows, profile)
    overview = {
        "league_id": str(league_id),
        "league_name": (readiness.get("league") or {}).get("name"),
        "season": int(season),
        "format": profile_format(profile),
        "teams": team_count(profile),
        "roster_positions": roster_positions(profile),
        "superflex": any(s in {"SUPER_FLEX", "SUPERFLEX", "SF"} for s in roster_positions(profile)) or roster_positions(profile).count("QB") >= 2,
        "dst_enabled": (positions.get("DST") or {}).get("decision") != "NOT_APPLICABLE",
        "k_enabled": (positions.get("K") or {}).get("decision") != "NOT_APPLICABLE",
        "scoring": _score_overview(profile),
        "adp_key": (readiness.get("market") or {}).get("adp_key"),
        "pipeline_status": (readiness.get("pipeline") or {}).get("status"),
        "pipeline_fingerprint": (readiness.get("pipeline") or {}).get("pipeline_fingerprint"),
    }
    evals = {}
    for pos, meta in positions.items():
        evals[pos] = {
            "selected_model": meta.get("selected_production_model"),
            "research_challenger": meta.get("best_research_challenger"),
            "validation_status": meta.get("decision"),
            "exact_scoring": meta.get("exact_scoring"),
            "reason": meta.get("reason"),
            "evidence": meta.get("evidence"),
            "replacement_points": ((readiness.get("league_value") or {}).get("replacement") or {}).get(pos),
        }
    report = {
        "schema": REPORT_SCHEMA,
        "schema_version": 1,
        "league_id": str(league_id),
        "season": int(season),
        "overview": overview,
        "position_evaluation": evals,
        "top": top,
        "outliers_top100": outliers,
        "sleepers_gt100": sleepers,
        "governance": {
            "adp_in_football_model": False,
            "automatic_promotion": False,
            "report_calculates_new_rank": False,
            "special_teams_projection_scope": "WEEKLY_CURRENT",
        },
    }
    summary = {
        "schema": "fie-league-research-report-summary-v1",
        "league_id": str(league_id), "season": int(season),
        "headline": {
            "pipeline_status": overview["pipeline_status"],
            "selected_models": {p: (positions.get(p) or {}).get("selected_production_model") for p in TOP_N},
            "actionable_top100_positive": len(outliers["positive"]),
            "actionable_top100_negative": len(outliers["negative"]),
            "positive_sleepers_gt100": sum(len(v) for v in sleepers.values()),
        },
        "top": top,
        "outliers_top100": outliers,
        "sleepers_gt100": sleepers,
        "position_models": {p: {k: (positions.get(p) or {}).get(k) for k in ("selected_production_model", "best_research_challenger", "decision", "reason", "exact_scoring")} for p in TOP_N},
    }
    return report, summary, _markdown(report)


def _fmt(v: Any, digits: int = 1) -> str:
    x = finite(v)
    return "—" if x is None else f"{x:.{digits}f}".rstrip("0").rstrip(".")


def _md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("|", "/") for x in row) + " |")
    return out


def _player_table(rows: list[dict]) -> list[str]:
    body=[]
    for i,r in enumerate(rows,1):
        body.append([
            int(r.get("position_rank") or i), r.get("name") or "—", r.get("team") or "—",
            _fmt(r.get("projection_points")), _fmt(r.get("p10")), _fmt(r.get("p90")),
            _fmt(r.get("vorp")), _fmt(r.get("adp")), _fmt(r.get("market_position_rank"),0),
            _fmt(r.get("rank_edge_position"),0), r.get("value_label") or "—", r.get("model_selected") or "—",
        ])
    return _md_table(["Rank","Player","Team","Projection","P10","P90","VORP","ADP","Market Pos Rank","Rank Edge","Value","Model"], body)


def _markdown(report: dict) -> str:
    o=report["overview"]; lines=[
        f"# FIE League Research Report — {o.get('league_name') or o['league_id']}", "",
        f"Season: **{o['season']}**  ", f"League ID: `{o['league_id']}`  ", f"Format: **{o['format']}**  ",
        f"Teams: **{o['teams']}**  ", f"Roster: `{', '.join(o['roster_positions'])}`  ",
        f"ADP market: `{o.get('adp_key') or 'unavailable'}`  ", f"Pipeline: **{o.get('pipeline_status')}**", "",
        "## Model overview", "",
    ]
    model_rows=[]
    for pos,meta in report["position_evaluation"].items():
        if pos not in TOP_N: continue
        model_rows.append([pos,meta.get("selected_model") or "—",meta.get("research_challenger") or "—",meta.get("validation_status") or "—",str(meta.get("exact_scoring")),meta.get("reason") or "—"])
    lines += _md_table(["Position","Selected Model","Research Challenger","Validation Status","Exact Scoring","Key Reason"],model_rows)
    lines += ["", "## League/scoring overview", "",
              f"PPR: **{o['scoring']['ppr_label']}** ({_fmt(o['scoring']['receptions'])} per reception)  ",
              f"Pass TD: **{_fmt(o['scoring']['pass_td'])}** · Pass INT: **{_fmt(o['scoring']['pass_int'])}**  ",
              f"Fumble: **{_fmt(o['scoring']['fumble'])}** · Fumble lost: **{_fmt(o['scoring']['fumble_lost'])}**  ",
              f"Superflex/2QB: **{'Yes' if o['superflex'] else 'No'}** · D/ST: **{'Yes' if o['dst_enabled'] else 'No'}** · K: **{'Yes' if o['k_enabled'] else 'No'}**", ""]
    if o["scoring"]["bonuses"]:
        lines += ["Bonuses: `" + json.dumps(o["scoring"]["bonuses"], sort_keys=True) + "`", ""]
    lines += ["## Position-by-position evaluation", ""]
    for pos in TOP_N:
        meta=report["position_evaluation"].get(pos)
        if not meta or meta.get("validation_status")=="NOT_APPLICABLE": continue
        lines += [f"### {pos}", "", f"Selected model: **{meta.get('selected_model') or '—'}**  ", f"Research challenger: **{meta.get('research_challenger') or '—'}**  ", f"Status: **{meta.get('validation_status')}**  ", f"Exact scoring: **{meta.get('exact_scoring')}**  ", f"Reason: {meta.get('reason') or '—'}  ", f"League replacement: **{_fmt(meta.get('replacement_points'))}**", ""]
        lines += _player_table(report["top"].get(pos,[])) + [""]
    lines += ["## Top-100 ADP positive outliers", ""]
    lines += _player_table(report["outliers_top100"]["positive"]) + [""]
    lines += ["## Top-100 ADP negative outliers / fades", ""]
    lines += _player_table(report["outliers_top100"]["negative"]) + [""]
    lines += ["## Positive sleepers with ADP >100", ""]
    for pos in ("QB","RB","WR","TE"):
        lines += [f"### {pos}", ""]
        rows=report["sleepers_gt100"].get(pos,[])
        body=[]
        for r in rows:
            body.append([_fmt(r.get("adp")),r.get("name"),r.get("team") or "—",_fmt(r.get("position_rank"),0),_fmt(r.get("market_position_rank"),0),_fmt(r.get("rank_edge_position"),0),_fmt(r.get("projection_points")),_fmt(r.get("vorp")),_fmt(r.get("confidence"),0),", ".join(r.get("why") or [])])
        lines += _md_table(["ADP","Player","Team","FIE Rank","Market Pos Rank","Edge","Projection","VORP","Confidence","Why"],body) + [""]
    lines += ["## Governance", "", "- ADP remains outside the football model.", "- This report does not calculate or activate a parallel ranking model.", "- Promotion-review-ready research remains non-production until a separate governance decision.", "- D/ST and K tables use the existing dedicated current specialist engines and are explicitly weekly/current in scope.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--league-id",required=True); ap.add_argument("--season",type=int,required=True); ap.add_argument("--output-dir",default="")
    a=ap.parse_args(argv); out=Path(a.output_dir) if a.output_dir else pipeline_dir(a.league_id,a.season)
    readiness=load_json(out/"readiness.json",{}); board_path=out/"final_player_board.csv"
    if not readiness or not board_path.is_file(): raise SystemExit("readiness.json and final_player_board.csv required")
    board=pd.read_csv(board_path,low_memory=False); report,summary,md=build_report(a.league_id,a.season,readiness,board)
    write_json(out/"league-report.json",report); write_json(out/"report-summary.json",summary,pretty=False); (out/"league-report.md").write_text(md,encoding="utf-8")
    print(json.dumps({"league_id":a.league_id,"top_counts":{k:len(v) for k,v in report["top"].items()},"top100_positive":len(report["outliers_top100"]["positive"]),"top100_negative":len(report["outliers_top100"]["negative"]),"sleepers":sum(len(v) for v in report["sleepers_gt100"].values())},indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())
