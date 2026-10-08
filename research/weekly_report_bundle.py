#!/usr/bin/env python3
"""Read-only weekly product coverage and existing owner outputs, never new advice."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from weekly_evidence_audit import stamp, digest

PRODUCTS = {
    "PLAYER_PERFORMANCE": "Publish all-game team/player usage and outcome evidence after games finalize.",
    "WAIVER_GUIDE": "Resolve Window 1D league/model blockers; preserve Chopped-first priority.",
    "EXPOSURE": "Capture and build PR2 lineups to populate scoring-isolated portfolio exposure.",
    "START_SIT": "Resolve PR2/Window 1C league eligibility and lineup evidence gaps.",
    "DST_HOLD_STREAM": "Publish the governed D/ST hold-versus-stream owner output.",
    "K_HOLD_STREAM": "Publish the governed kicker hold-versus-stream owner output.",
    "POST_WEEK_REVIEW": "Publish realized outcomes and paired FIE/Sleeper decision evaluation for this week.",
}


def bind_pr2_capture(root: Path, path: Path, value: dict) -> dict:
    """Replay the existing owner's immutable identity, never a new lineup solve."""
    from in_season_pr2_weekly_lineups import capture_payload, sha256_value
    expected = sha256_value(capture_payload(value))
    if value.get("capture_content_sha256") != expected or value.get("capture_id") != expected[:16]:
        raise ValueError("PR2_CAPTURE_IDENTITY_MISMATCH")
    capture = path.parent / "captures" / f"portfolio-{expected[:16]}.json"
    if not capture.is_file():
        raise ValueError("PR2_IMMUTABLE_CAPTURE_MISSING")
    frozen = json.loads(capture.read_text(encoding="utf-8"))
    if frozen.get("capture_content_sha256") != expected or frozen.get("capture_id") != expected[:16] or sha256_value(capture_payload(frozen)) != expected:
        raise ValueError("PR2_IMMUTABLE_CAPTURE_REPLAY_MISMATCH")
    # The established writer may refresh generated_at on an identical payload.
    # Preserve that allowed volatility; the original publication cannot lie
    # after the validated latest pointer's generation clock.
    if stamp(frozen["generated_at"]) > stamp(value["generated_at"]):
        raise ValueError("PR2_IMMUTABLE_CAPTURE_AFTER_LATEST")
    return {"capture_id": expected[:16], "capture_content_sha256": expected,
            "capture_path": capture.relative_to(root).as_posix(), "capture_sha256": digest(capture)}


def captured_opponent_contexts(pr2: dict) -> list[dict]:
    """Display unchanged captured H2H owner context; never infer a field."""
    rows = []
    for league in pr2["leagues"]:
        context = {"league_id": league["league_id"], "league_name": league.get("league_name"),
                   "season": league["season"], "week": league["week"],
                   "scoring_signature": (league.get("evidence") or {}).get("scoring_signature"),
                   "capture_id": pr2["capture_id"], "actionable": False}
        if league.get("format") == "CHOPPED":
            rows.append({**context, "kind": "CHOPPED_FIELD", "status": "BLOCKED_CAPTURED_ACTIVE_FIELD_REQUIRED", "owner_context": None})
            continue
        owner = league.get("opponent_context")
        if not isinstance(owner, dict): owner = {"status": "NOT_YET_CAPTURED"}
        rows.append({**context, "kind": "DIRECT_H2H", "status": owner.get("status", "NOT_YET_CAPTURED"),
                     "owner_context": owner, "basis": "Unchanged PR2 context. Exact maximum-mean advisory is not an opponent submitted lineup or intention."})
    return rows


def load_owner(root: Path, path: Path, season: int, week: int, as_of: datetime, expected_schema: str | None = None) -> tuple[dict | None, dict]:
    binding = {"path": path.relative_to(root).as_posix()}
    if not path.is_file():
        return None, {**binding, "status": "MISSING"}
    binding["sha256"] = digest(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        observed = stamp(value.get("as_of_utc") or value["generated_at"])
        generated = stamp(value.get("generated_at") or observed.isoformat())
        if max(observed, generated) > as_of:
            raise ValueError("REPORT_AFTER_AS_OF")
        if as_of - observed > timedelta(hours=36):
            raise ValueError("REPORT_STALE_OVER_36_HOURS")
        if value.get("schema") not in {"fie-window1c-weekly-actions-portfolio-v1", "fie-window1d-optimal-waiver-portfolio-v1", "fie-in-season-pr2-weekly-lineup-portfolio-v1"}:
            raise ValueError("REPORT_SCHEMA_MISMATCH")
        if expected_schema is not None and value.get("schema") != expected_schema:
            raise ValueError("REPORT_OWNER_SCHEMA_MISMATCH")
        leagues = value["leagues"]
        if not isinstance(leagues, list) or not leagues:
            raise ValueError("REPORT_EMPTY_LEAGUE_SCOPE")
        ids = [str(row["league_id"]) for row in leagues]
        if len(set(ids)) != len(ids):
            raise ValueError("REPORT_DUPLICATE_LEAGUE")
        # PR2 portfolio target identity lives in its league records.
        if "season" in value and (value["season"], value["week"]) != (season, week):
            raise ValueError("REPORT_TARGET_MISMATCH")
        for row in leagues:
            if (row.get("season"), row.get("week")) != (season, week):
                raise ValueError("REPORT_LEAGUE_TARGET_MISMATCH")
        capture_binding = bind_pr2_capture(root, path, value) if expected_schema == "fie-in-season-pr2-weekly-lineup-portfolio-v1" else {}
        return value, {**binding, **capture_binding, "status": "AVAILABLE", "observed_at": observed.isoformat(), "generated_at": value.get("generated_at"), "league_ids": sorted(ids)}
    except Exception as exc:
        return None, {**binding, "status": "BLOCKED_INVALID_SOURCE", "reason": f"{type(exc).__name__}:{exc}"}


def bundle(root: Path, season: int, week: int, as_of: datetime, portfolio_surface: Path | None = None) -> dict:
    if as_of.tzinfo is None or not 1 <= week <= 18:
        raise ValueError("REPORT_TARGET_OR_TIME_INVALID")
    base = root / f"data/research/evaluation/{season}/weeks/week-{week}"
    owners = {
        "WINDOW_1C": base / "weekly-actions-portfolio-v1.json",
        "WINDOW_1D": base / "waivers/portfolio-latest.json",
        "PR2": base / "lineups/portfolio-latest.json",
    }
    schemas = {"WINDOW_1C":"fie-window1c-weekly-actions-portfolio-v1", "WINDOW_1D":"fie-window1d-optimal-waiver-portfolio-v1", "PR2":"fie-in-season-pr2-weekly-lineup-portfolio-v1"}
    payloads, bindings = {}, {}
    for owner, path in owners.items():
        payloads[owner], bindings[owner] = load_owner(root, path, season, week, as_of, expected_schema=schemas[owner])
    products = {key: {"status": "BLOCKED_MISSING_PRODUCT", "next_action": action,
                      "complete": False, "owner_sources": [], "content": None}
                for key, action in PRODUCTS.items()}
    def attach(product, owner, content):
        products[product].update(status="PARTIAL_OWNER_OUTPUT", owner_sources=[owner], content=content)
    c = payloads["WINDOW_1C"]
    d = payloads["WINDOW_1D"]
    pr2 = payloads["PR2"]
    if c:
        attach("START_SIT", "WINDOW_1C", [{"league_id": row["league_id"], "league_name": row.get("league_name"),
            "status": row["status"], "action_status": row.get("action_status"),
            "lineup_alerts": (row.get("actions") or {}).get("lineup", []),
            "injury_alerts": (row.get("actions") or {}).get("injury_alerts", [])} for row in c["leagues"]])
    if d:
        leagues = sorted(d["leagues"], key=lambda row: (0 if row.get("format") == "CHOPPED" else 1, str(row["league_id"])))
        attach("WAIVER_GUIDE", "WINDOW_1D", {"operational_readiness": d.get("operational_readiness"), "leagues": leagues})
    if pr2:
        intelligence = pr2.get("portfolio_intelligence")
        if isinstance(intelligence, dict) and isinstance(intelligence.get("cross_league_exposure"), list):
            attach("EXPOSURE", "PR2", {**intelligence, "captured_opponent_contexts": captured_opponent_contexts(pr2)})
        products["START_SIT"]["owner_sources"].append("PR2")
        products["START_SIT"].update(status="PARTIAL_OWNER_OUTPUT", pr2_leagues=pr2["leagues"])
    if portfolio_surface is not None:
        path = portfolio_surface.resolve()
        binding = {"path": path.relative_to(root).as_posix(), "sha256": digest(path)}
        try:
            surface = json.loads(path.read_text(encoding="utf-8"))
            if surface.get("schema") != "fie-weekly-portfolio-surface-v1" or (surface.get("season"),surface.get("week")) != (season,week):
                raise ValueError("PORTFOLIO_SURFACE_TARGET_OR_SCHEMA_MISMATCH")
            observed = stamp(surface["as_of_utc"])
            if observed > as_of or as_of-observed > timedelta(hours=36):
                raise ValueError("PORTFOLIO_SURFACE_FUTURE_OR_STALE")
            if not any(row.get("status") in {"BOUND_CURRENT_ROSTER","PARTIAL_UNRESOLVED_PLAYERS"} for row in surface.get("leagues",[])):
                raise ValueError("PORTFOLIO_SURFACE_NO_BOUND_LEAGUES")
            if not isinstance(surface.get("roster_exposure"),list) or not surface.get("input_hashes"):
                raise ValueError("PORTFOLIO_SURFACE_LINEAGE_MISSING")
            for relative, expected in surface["input_hashes"].items():
                source = (root/relative).resolve()
                if not source.is_relative_to(root) or digest(source) != expected:
                    raise ValueError("PORTFOLIO_SURFACE_INPUT_CHANGED")
            bindings["CURRENT_PORTFOLIO"] = {**binding,"status":"AVAILABLE","observed_at":observed.isoformat()}
            attach("EXPOSURE","CURRENT_PORTFOLIO",{"roster_exposure":surface["roster_exposure"],
                "league_status_counts":surface["league_status_counts"],
                "opponent_exposure":[{"league_id":league["league_id"],**league.get("opponent_exposure",{"status":"BLOCKED_LEAGUE_INPUTS"})} for league in surface["leagues"]], "scope":"Stored active-roster and starter observations; no proposed lineup or opponent inference"})
            for product, label, positions in [("DST_HOLD_STREAM","DST",{"DEF","DST","D/ST"}),("K_HOLD_STREAM","K",{"K"})]:
                boards=(surface.get("specialist_evidence") or {}).get(label)
                if isinstance(boards,list) and boards:
                    content={"forecast_boards":boards,"hold_stream_strategy_validated":False}
                    if d:
                        content["existing_waiver_owner_recommendations"]=[{"league_id":league["league_id"],
                            "recommendations":[row for row in league.get("recommendations",[]) if row.get("position") in positions]}
                            for league in d["leagues"]]
                    attach(product,"CURRENT_PORTFOLIO",content)
            if pr2:
                products["EXPOSURE"]["owner_sources"].append("PR2")
                products["EXPOSURE"]["content"]["pr2_intelligence"] = pr2.get("portfolio_intelligence")
                products["EXPOSURE"]["content"]["captured_opponent_contexts"] = captured_opponent_contexts(pr2)
                from weekly_opponent_exposure import captured_exposure
                try:
                    products["EXPOSURE"]["content"]["captured_opponent_exposure"] = captured_exposure(pr2, surface, bindings["PR2"])
                except Exception as exc:
                    bindings["OPPONENT_EXPOSURE"] = {"status": "BLOCKED_CAPTURE_JOIN", "reason": f"{type(exc).__name__}:{exc}"}
        except Exception as exc:
            bindings["CURRENT_PORTFOLIO"] = {**binding,"status":"BLOCKED_INVALID_SOURCE","reason":f"{type(exc).__name__}:{exc}"}
            products["EXPOSURE"]["next_action"] = "Inspect CURRENT_PORTFOLIO rejection; for stale core snapshots run Refresh Currentseason, then Window 1C and its automatic Window 1D follow-up. Preserve freshness and profile guards."
    # Outcome products are not due while the target week's postgame buffer is
    # still open. Previous-week reports remain distinct artifacts.
    try:
        from weekly_evidence_audit import schedule
        from resolve_in_season_pr2_lineup_outcome_target import STABILIZATION_HOURS
        games, _ = schedule(root, season, week, as_of)
        outcomes_due = max(stamp(game["kickoff_at"]) for game in games) + timedelta(hours=STABILIZATION_HOURS)
        if as_of < outcomes_due:
            for name in ("PLAYER_PERFORMANCE", "POST_WEEK_REVIEW"):
                products[name].update(status="NOT_DUE", outcomes_eligible_at=outcomes_due.isoformat(),
                                      next_action="Wait for the established postgame stabilization buffer; do not create target-week outcomes early.")
        else:
            from weekly_lineup_review import review
            post_review = review(root, season, week, as_of, outcomes_due)
            bindings["POST_WEEK_REVIEW"] = {"status": post_review["status"], "blocked_revisions": post_review["blocked_revisions"]}
            if post_review["revisions"]:
                attach("POST_WEEK_REVIEW", "PR2_OUTCOME_EVALUATOR", post_review)
            reports = []
            for path in (root / f"data/operations/weekly-performance/{season}/week_{week:02d}/reports").glob("*.json"):
                value = json.loads(path.read_text(encoding="utf-8"))
                observed = stamp(value["as_of_utc"])
                if observed <= as_of:
                    reports.append((observed, path, value))
            if reports:
                _, path, value = max(reports, key=lambda row:(row[0],str(row[1])))
                from weekly_player_performance import build as replay_performance
                source_path = root / value["source"]["path"]
                replayed = replay_performance(root, source_path, season, week, stamp(value["as_of_utc"]))
                from weekly_player_performance import replay_matches
                if not replay_matches(value, replayed):
                    raise ValueError("PERFORMANCE_REPORT_REPLAY_MISMATCH")
                bindings["PLAYER_PERFORMANCE"] = {"path":path.relative_to(root).as_posix(),"sha256":digest(path),"status":"AVAILABLE"}
                attach("PLAYER_PERFORMANCE","PLAYER_PERFORMANCE",{"report_path":path.relative_to(root).as_posix(),
                    "game_count":value["game_count"],"player_game_count":value["player_game_count"],"owner_status":value["status"],
                    "official_game_finality_certified":False})
    except Exception as exc:
        bindings["OUTCOME_PRODUCT_TIMING"] = {"status":"BLOCKED_INVALID_SOURCE","reason":f"{type(exc).__name__}:{exc}"}
    return {"schema": "fie-weekly-report-bundle-v1", "season": season, "week": week,
        "as_of_utc": as_of.isoformat(), "status": "INCOMPLETE", "complete_product_count": 0,
        "required_product_count": len(PRODUCTS), "products": products, "sources": bindings,
        "governance": {"read_only": True, "network_access": False, "new_recommendations": False,
                       "cross_league_decision_transfer": False, "production_model_changed": False},
        "note": "Existing partial owner outputs are included for inspection. A source file or successful workflow does not certify a complete weekly product. Missing products remain explicit; prior-week reviews are not relabeled as this week's outcomes."}


def markdown(report: dict) -> str:
    lines = [f"## Weekly report coverage — {report['season']} Week {report['week']}",
             f"**{report['status']}** — {report['complete_product_count']}/{report['required_product_count']} complete products.", "",
             "| Required product | Coverage | Next action |", "|---|---|---|"]
    lines.extend(f"| {key} | {row['status']} | {row['next_action']} |" for key, row in report["products"].items())
    lines += ["", report["note"], "", "### Owner sources", ""]
    for owner, row in report["sources"].items():
        lines.append(f"- {owner}: **{row['status']}** — `{row.get('path', '—')}`" + (f" — {row['reason']}" if row.get("reason") else ""))
    contexts = (report["products"]["EXPOSURE"].get("content") or {}).get("captured_opponent_contexts", [])
    if contexts:
        lines += ["", "### Captured opponent context", "", "| League | Scope | Capture state |", "|---|---|---|"]
        lines.extend(f"| {row['league_id']} | {row['kind']} | {row['status']} |" for row in contexts)
        lines += ["", "Opponent maximum-mean advisory is distinct from observed submitted starters. Chopped requires captured active-field evidence; no H2H pairing substitutes for it."]
    observed = (report["products"]["EXPOSURE"].get("content") or {}).get("captured_opponent_exposure")
    if observed:
        lines += ["", "### Observed H2H opponent starter exposure", "",
                  "| League | Scope | Join state |", "|---|---|---|"]
        lines.extend(f"| {row['league_name'] or row['league_id']} | {row['kind']} | {row['status']} |" for row in observed["leagues"])
        lines += ["",
                  "| Player | Opponent-start leagues |", "|---|---:|"]
        lines.extend(f"| {row['player_name'] or row['player_id']} | {row['opponent_start_league_count']} |" for row in observed["players"])
        if not observed["players"]:
            lines.append("| No bound submitted starters | 0 |")
        lines += ["", "These are captured submitted starters, not final lineups or predicted opponent actions. Chopped-field exposure remains separate."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--as-of-utc", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--portfolio-surface", type=Path)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    if output.is_relative_to(root / "data/research"):
        raise ValueError("REPORT_BUNDLE_MUST_NOT_OVERWRITE_RESEARCH_EVIDENCE")
    report = bundle(root, args.season, args.week, stamp(args.as_of_utc) if args.as_of_utc else datetime.now(timezone.utc), portfolio_surface=args.portfolio_surface)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    path = output.with_suffix(".md")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(markdown(report))
    print(markdown(report))

if __name__ == "__main__":
    main()
