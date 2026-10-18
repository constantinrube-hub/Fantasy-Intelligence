/* FIE UI replay scenarios. Each scenario binds one immutable capture to a
 * frozen browser clock. Overrides may only alter *provider payloads* to model a
 * provider state (for example a newer live week); they never touch app state. */
'use strict';
const W6_PREKICKOFF = 'data/research/prospective/weekly-sources/2026/week_06/20261015T174631408136Z';
const SEASON_MARKET = 'data/research/market/sleeper/2026/season_market_2026-09-30.jsonl.gz';

const REFERENCE_LEAGUES = {
  redraft: '1313697754907697152',   // ReDraft – Pro XVI (16 teams, 1QB, DEF)
  dynastySF: '1316165875291668480', // Genesis Dynasty (SF, K, multiple flex types)
  chopped: '1313696967989157888',   // Chopped – Drive (18 rosters, 5 eliminated after Week 5)
  bestBall: '1314007486205804544',  // BestBall – Pro XVI
  dynasty: '1312066407394975744',   // Stoned Lack Dynasty 29
  idpDynasty: '1331042152091766784', // Stoned Lack IDP Dynasty 39 (submitted TE starter Out at capture time)
  dynasty30: '1335691030116184065', // Stoned Lack Dynasty 30 (live rosters differ from the research snapshot → live overlay rebuild)
  dynastyPrime: '1314002567004459008' // Dynasty - Prime XVI (live roster has a healthy, projected player in an IR slot)
};

const nflState = (week) => ({ week, leg: week, season: '2026', season_type: 'regular', league_season: '2026',
  previous_season: '2025', season_start_date: '2026-09-09', display_week: week, league_create_season: '2026', season_has_scores: true });

const SCENARIOS = {
  // Thursday of Week 6, ~6 h before the first kickoff: the canonical pregame state.
  'w6-pregame': {
    capture: W6_PREKICKOFF, seasonMarket: SEASON_MARKET, clock: '2026-10-15T18:00:00Z', week: 6,
    nflState: nflState(6), overrides: {}
  },
  // Saturday of Week 6: TNF is final, Sunday games are still unlocked.
  'w6-after-tnf': {
    capture: W6_PREKICKOFF, seasonMarket: SEASON_MARKET, clock: '2026-10-17T12:00:00Z', week: 6,
    nflState: nflState(6), overrides: {}
  },
  // Provider is one week ahead of the bundled research snapshot (stale-bundle model).
  'live-week-ahead': {
    capture: W6_PREKICKOFF, seasonMarket: SEASON_MARKET, clock: '2026-10-15T18:00:00Z', week: 7,
    nflState: nflState(7),
    overrides: {
      league: (league) => ({ ...league, settings: { ...(league.settings || {}), leg: 7, last_scored_leg: 6 } })
    }
  }
};

module.exports = { SCENARIOS, REFERENCE_LEAGUES, W6_PREKICKOFF, SEASON_MARKET };
