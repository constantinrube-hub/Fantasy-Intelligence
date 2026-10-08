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


def load_owner(root: Path, path: Path, season: int, week: int, as_of: datetime) -> tuple[dict | None, dict]:
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
        return value, {**binding, "status": "AVAILABLE", "observed_at": observed.isoformat(), "league_ids": sorted(ids)}
    except Exception as exc:
        return None, {**binding, "status": "BLOCKED_INVALID_SOURCE", "reason": f"{type(exc).__name__}:{exc}"}


def bundle(root: Path, season: int, week: int, as_of: datetime) -> dict:
    if as_of.tzinfo is None or not 1 <= week <= 18:
        raise ValueError("REPORT_TARGET_OR_TIME_INVALID")
    base = root / f"data/research/evaluation/{season}/weeks/week-{week}"
    owners = {
        "WINDOW_1C": base / "weekly-actions-portfolio-v1.json",
        "WINDOW_1D": base / "waivers/portfolio-latest.json",
        "PR2": base / "lineups/portfolio-latest.json",
    }
    payloads, bindings = {}, {}
    for owner, path in owners.items():
        payloads[owner], bindings[owner] = load_owner(root, path, season, week, as_of)
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
            attach("EXPOSURE", "PR2", intelligence)
        products["START_SIT"]["owner_sources"].append("PR2")
        products["START_SIT"].update(status="PARTIAL_OWNER_OUTPUT", pr2_leagues=pr2["leagues"])
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
        lines.append(f"- {owner}: **{row['status']}** — `{row['path']}`" + (f" — {row['reason']}" if row.get("reason") else ""))
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--as-of-utc", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    if output.is_relative_to(root / "data/research"):
        raise ValueError("REPORT_BUNDLE_MUST_NOT_OVERWRITE_RESEARCH_EVIDENCE")
    report = bundle(root, args.season, args.week, stamp(args.as_of_utc) if args.as_of_utc else datetime.now(timezone.utc))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(markdown(report))

if __name__ == "__main__":
    main()
