#!/usr/bin/env python3
"""Portfolio Home modular integration and league-isolation guards."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
portfolio=(ROOT/'app'/'portfolio-home.js').read_text(encoding='utf-8')
decisions=(ROOT/'app'/'decision-engines.js').read_text(encoding='utf-8')
config=(ROOT/'app'/'portfolio-config.js').read_text(encoding='utf-8')

# Portfolio is intentionally modular; do not require literal script tags in
# the legacy source shell.
assert "const SNAP_KEY='fiePortfolioSnapshotsV1'" in portfolio
assert 'Portfolio.snapshots[String(snapshot.leagueId)]' in portfolio
assert 'function refreshOne(e)' in portfolio
assert 'function captureCurrentLeague(' in portfolio
assert 'window.FIEPortfolio' in portfolio

refresh_body=portfolio.split('async function refreshOne(e)',1)[1].split('async function refreshStatuses',1)[0]
assert 'state.league=' not in refresh_body,'status refresh must not mutate active league state'
assert 'openLeague(card.dataset.leagueId,route)' in portfolio

# Decision engine snapshots remain explicitly namespaced by League ID.
assert "leagueId:String(state.league.league_id||'')" in decisions
assert 'Engine.portfolioSnapshot=portfolioSnapshot' in decisions
assert 'window.FIEPortfolio?.captureCurrentLeague?.(portfolioSnapshot' in decisions

# Managed leagues remain server/config backed.
assert 'managedLeagues' in config and 'mergeManagedIntoLocal' in config

print('OK: Portfolio Home is League-ID cached, non-mutating during status refresh, and modularly wired to decision engines')
