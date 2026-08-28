#!/usr/bin/env python3
"""Static integration guards for the modular decision-engine frontend."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENGINE_PATH=ROOT/"app"/"decision-engines.js"
UI_PATH=ROOT/"app"/"decision-ui.js"
ENGINE=ENGINE_PATH.read_text(encoding="utf-8")
UI=UI_PATH.read_text(encoding="utf-8")

def require(text,needle,label):
    assert needle in text,f"missing {label}: {needle!r}"

def main():
    assert ENGINE_PATH.exists(),"decision engine module missing"
    assert UI_PATH.exists(),"decision UI module missing"

    # Public engine API and major simulations remain available.
    for fn in (
        "runDraftMonteCarlo",
        "runDraftMonteCarloAsync",
        "runLeagueSimulation",
        "simulateRedraftSeason",
        "simulateChopped",
        "renderMatchupPanel",
        "portfolioSnapshot",
    ):
        require(ENGINE,fn,fn)

    # The draft simulation uses actual final-roster utility and manager/need context.
    require(ENGINE,"rosterUtilityFromPool","format-specific final roster utility")
    require(ENGINE,"managerReach","manager tendency adjustment")
    require(ENGINE,"needAdjustment","dynamic roster-need adjustment")

    # Weekly engine explicitly surfaces uncertainty and matchup odds.
    require(ENGINE,"matchupProbability","matchup win probability")
    require(ENGINE,"p10Margin","lower uncertainty band")
    require(ENGINE,"p90Margin","upper uncertainty band")

    # Chopped is simulated as elimination.
    require(ENGINE,"eliminatedPerPeriod","chopped elimination count")
    require(ENGINE,"topReleased","released-player redistribution")

    # Current modular UI owns the matchup surface rather than a literal old nav
    # declaration in index.html.
    require(UI,"matchupSimPanel","matchup panel registration")
    require(UI,"Modeled win probability","weekly matchup probability surface")

    # Engine must expose one modular API object.
    require(ENGINE,"window.FIEDecisionEngines=Engine","decision engine export")

    print("OK decision-engine modular integration")

if __name__=="__main__":
    main()
