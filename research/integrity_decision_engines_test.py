#!/usr/bin/env python3
"""Static integration guards for the modular decision-engine frontend.

These checks deliberately avoid a browser dependency in CI. They protect the
contract between the stable single-file runtime and app/decision-engines.js;
browser/E2E tests can be layered on top later.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ENGINE_PATH = ROOT / "app" / "decision-engines.js"
ENGINE = ENGINE_PATH.read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"missing {label}: {needle!r}"


def main() -> None:
    assert ENGINE_PATH.exists(), "decision engine module missing"
    require(INDEX, '<script src="app/decision-engines.js"></script>', "decision engine script include")
    require(INDEX, "window.FIE_DRAFT_V71=", "draft helper compatibility export")
    require(INDEX, "['matchupsim','Matchup & Playoffs']", "weekly simulation navigation")
    require(INDEX, "m5DecisionFormatValidated", "decision-specific M5 format gate")
    require(INDEX, "m5WeeklyBaseEligible", "weekly activation gate")
    require(INDEX, "m5WaiverBaseEligible", "waiver activation gate")

    # Public engine API and major simulations must remain available.
    for fn in (
        "runDraftMonteCarlo",
        "runLeagueSimulation",
        "simulateRedraftSeason",
        "simulateChopped",
        "renderMatchupPanel",
    ):
        require(ENGINE, fn, fn)

    # The draft simulation must use the actual final-roster utility rather than
    # collapsing back to a standalone player rank.
    require(ENGINE, "rosterUtilityFromPool", "format-specific final roster utility")
    require(ENGINE, "managerReach", "manager tendency adjustment")
    require(ENGINE, "needAdjustment", "dynamic roster-need adjustment")

    # The weekly engine must explicitly surface uncertainty and matchup odds.
    require(ENGINE, "matchupProbability", "matchup win probability")
    require(ENGINE, "p10Margin", "lower uncertainty band")
    require(ENGINE, "p90Margin", "upper uncertainty band")

    # Chopped must be simulated as elimination, not merely relabelled floor.
    require(ENGINE, "eliminatedPerPeriod", "chopped elimination count")
    require(ENGINE, "topReleased", "released-player redistribution")

    print("OK decision-engine static integration")


if __name__ == "__main__":
    main()
