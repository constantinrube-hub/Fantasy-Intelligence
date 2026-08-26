from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text()
portfolio=(ROOT/'app'/'portfolio-home.js').read_text()
decisions=(ROOT/'app'/'decision-engines.js').read_text()

assert '<script src="app/decision-engines.js"></script>' in html
assert '<script src="app/portfolio-home.js"></script>' in html
assert html.index('app/decision-engines.js') < html.index('app/portfolio-home.js')
assert "const SNAP_KEY='fiePortfolioSnapshotsV1'" in portfolio
assert 'Portfolio.snapshots[String(snapshot.leagueId)]' in portfolio
assert 'function refreshOne(e)' in portfolio
refresh_body=portfolio.split('async function refreshOne(e)',1)[1].split('async function refreshStatuses',1)[0]
assert 'state.league=' not in refresh_body, 'status refresh must not mutate active league state'
assert 'openLeague(card.dataset.leagueId,route)' in portfolio
assert "leagueId:String(state.league.league_id||'')" in decisions
assert 'Engine.portfolioSnapshot=portfolioSnapshot' in decisions
assert 'window.FIEPortfolio?.captureCurrentLeague?.(portfolioSnapshot' in decisions
print('OK: Portfolio Home is League-ID cached, non-mutating during all-league status refresh, and wired after decision engines')
