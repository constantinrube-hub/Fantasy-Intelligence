/* Phase 2: read-only Weekly presentation. Existing scoring/identity/optimizer owners remain authoritative. */
(function () {
  'use strict';
  const S = () => window.state || {};
  const n = v => v == null || typeof v === 'boolean' || String(v).trim() === '' ? null : (Number.isFinite(Number(v)) ? Number(v) : null);
  const pts = v => n(v) === null ? 'Unavailable' : `${n(v).toFixed(2)} pts`;
  const signed = v => n(v) === null ? 'Unavailable' : `${v > 0 ? '+' : ''}${n(v).toFixed(2)} pts`;
  const $ = id => document.getElementById(id);
  const node = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  const cache = new Map();
  let nfl = null, nflPromise = null, serial = 0, activeKey = '', timer = null;
  const scope = () => ({ leagueId: String(S().league?.league_id || ''), season: Number(window.activeSeason?.() || S().league?.season), week: Number(window.currentWeek?.() || 1), rosterId: String(S().selectedRoster || $('weeklyRosterPicker')?.value || '') });
  const keyFor = c => `${c.leagueId}|${c.season}|${c.week}|${c.rosterId}`;
  const contextText = c => `Season ${c.season} · Week ${c.week} · ${S().league?.name || c.leagueId} · ${rosterName(c.rosterId)}`;
  const starterSlots = () => window.FIECore?.PositionRegistry?.starterSlots?.(S().league?.roster_positions || []) || [];
  function rosterName(id) {
    const r = (S().rosters || []).find(r => String(r.roster_id) === String(id));
    const u = (S().users || []).find(u => u.user_id === r?.owner_id);
    return u?.metadata?.team_name || u?.display_name || u?.username || `Roster ${id}`;
  }
  function player(id) {
    const r = window.FIECore?.PlayerIdentity?.resolve?.(String(id));
    if (r?.status === 'resolved') return r.player;
    // Provider metadata may explain a reported ID; it cannot become a canonical optimizer candidate.
    const p = S().playerMap?.[String(id)];
    return p ? { name: p.full_name || [p.first_name, p.last_name].filter(Boolean).join(' ') || String(id), position: p.position, team: p.team, sleeperId: String(id), metadataOnly: true } : null;
  }
  function gamesFor(c) {
    return (S().weekly?.schedule || []).filter(g => Number(g.season) === c.season && Number(g.week) === c.week && String(g.game_type || g.season_type || 'REG').toUpperCase() === 'REG');
  }
  // nflverse gametime is America/New_York wall time. Never parse it in the viewer's timezone.
  function kickoff(g) {
    if (g?.kickoff || g?.start_time) { const t = Date.parse(g.kickoff || g.start_time); if (Number.isFinite(t)) return t; }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(g?.gameday)) || !/^\d{2}:\d{2}/.test(String(g?.gametime))) return null;
    const target = Date.parse(`${g.gameday}T${g.gametime.slice(0, 5)}:00Z`);
    let utc = target;
    for (let i = 0; i < 3; i++) {
      const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(utc)).map(p => [p.type, p.value]));
      const wall = Date.parse(`${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:00Z`);
      utc += target - wall;
    }
    return utc;
  }
  function period(c, nflState = nfl, games = gamesFor(c), now = Date.now()) {
    const season = n(nflState?.season), week = n(nflState?.display_week ?? nflState?.week);
    if (season !== null && c.season < season) return 'completed';
    if (season !== null && c.season > season) return 'upcoming';
    if (season === c.season && String(nflState?.season_type || '').toLowerCase() === 'regular' && week !== null) {
      if (c.week < week) return 'completed';
      if (c.week > week) return 'upcoming';
    }
    const starts = games.map(kickoff).filter(t => t !== null);
    if (starts.length === games.length && starts.length && Math.min(...starts) > now) return 'upcoming';
    if (starts.some(t => t <= now)) return 'live';
    return 'unknown';
  }
  function gameState(p, c) {
    const team = p?.team;
    if (!team) return 'Game state unavailable';
    const games = gamesFor(c), g = games.find(g => g.home_team === team || g.away_team === team || (team === 'LAR' && [g.home_team, g.away_team].includes('LA')));
    if (!g) return games.length >= 12 ? 'No scheduled game found' : 'Schedule unavailable';
    const k = kickoff(g);
    if (period(c) === 'completed') return 'Reported completed week';
    if (k === null) return 'Kickoff unverified';
    if (k > Date.now()) return `Not started · ${new Date(k).toLocaleString(undefined, { weekday: 'short', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' })}`;
    return 'Started · final status unverified';
  }
  function pairing(rows, id) {
    const mine = rows.find(r => String(r.roster_id) === String(id)) || null;
    const others = mine?.matchup_id == null ? [] : rows.filter(r => r.matchup_id === mine.matchup_id && String(r.roster_id) !== String(id));
    return { mine, opponent: others.length === 1 ? others[0] : null, multiple: others.length > 1 };
  }
  function reportedPlayers(row, slots = starterSlots()) {
    const starters = row?.starters || [];
    return starters.map((id, i) => {
      const empty = String(id) === '0' || id == null || String(id) === '';
      const p = empty ? null : player(id);
      const direct = n(row?.starters_points?.[i]);
      return { id: String(id ?? ''), slot: slots[i] || `Slot ${i + 1}`, name: empty ? 'Empty slot' : p?.name || p?.full_name || `Player ${id}`, position: p?.position || 'Unknown', p,
        actual: empty ? (direct === 0 ? 0 : null) : (direct ?? n(row?.players_points?.[String(id)])), empty };
    });
  }
  function rawStats(p, c) {
    if (!p || p.metadataOnly) return null;
    const source = [...(S().weekly?.weekly2026 || []), ...(S().weekly?.weekly2025 || [])];
    const identity = window.FIECore?.PlayerIdentity;
    // Normalize legacy browser GSIS field spelling only; canonical resolution still owns collisions.
    const normalized=(window.PLAYERS||[]).map(q=>({...q,gsis_id:q.gsis_id||q.gsisId||q.publicPlayerId})), index=identity?.index?.(normalized), id=identity?.governedId?.(p);
    const matches = source.filter(r => {if(Number(r.season)!==c.season||Number(r.week)!==c.week||String(r.season_type||'REG')!=='REG'||!id)return false;const resolved=identity?.resolve?.({gsis_id:r.player_id||r.gsis_id},{players:normalized,index});return resolved?.status==='resolved'&&resolved.id===id;});
    return matches.length === 1 ? matches[0] : null;
  }
  function scoring(p, c, actual) {
    const raw = rawStats(p, c), b = raw ? window.FIE89?.weeklyScoringBreakdown?.(raw, p) : null;
    if (!b) return { text: 'Unavailable · selected-week raw scoring inputs not loaded', exact: false, categories: [] };
    const available = b.categories.filter(x => x.points !== null);
    const subtotal = available.reduce((s, x) => s + x.points, 0);
    return { ...b, subtotal, discrepancy: b.exact && actual !== null ? actual - subtotal : null,
      text: `${b.exact ? 'Complete replay' : 'Partial replay'} · ${available.map(x => `${x.rule}: ${pts(x.points)}`).join('; ') || 'No supported categories'}${b.exact ? '' : ` · Missing: ${b.categories.filter(x => !x.supported).map(x => x.rule).join(', ')}`}` };
  }
  function forecastAvailability() {
    return 'Unavailable · no served forecast bound to this league, scoring profile, player, and verified pregame cutoff';
  }
  function performanceRow(x, c) {
    const b = scoring(x.p, c, x.actual), g = gameState(x.p, c);
    return { title: x.name, slot: x.slot, name: x.name, actual: pts(x.actual), game: g, context: contextText(c),
      expanded: [['Reported actual', pts(x.actual)], ['Scoring categories', b.text], ['Frozen pregame projection', forecastAvailability()], ['Actual − frozen projection', 'Unavailable'], ['Usage', usage(x.p, c)]],
      advanced: [['Source', 'Sleeper league matchup response; starters_points with players_points fallback'], ['League / roster', `${c.leagueId} / ${c.rosterId}`], ['Period', `${c.season} / week ${c.week}`], ['Player ID', x.id], ['Slot label', 'Selected-season league slot order; historical rule revisions are not archived'], ['Scoring replay status', b.exact ? 'Complete loaded-stat replay' : 'Incomplete / unavailable'], ['Replay subtotal', b.subtotal == null ? null : pts(b.subtotal)], ['Reported minus replay', b.discrepancy == null ? null : signed(b.discrepancy)], ['Raw scoring inputs', b.categories.map(r => `${r.rule}: quantity ${r.quantity ?? 'Unavailable'} × ${r.weight} = ${r.points ?? 'Unavailable'}; ${r.source || 'unavailable'}`).join('\n') || null], ['Forecast capture', forecastAvailability()], ['Corrections', 'Provider totals are reported values and may be corrected. A replay does not replace the reported score.']],
      note: 'Current browser estimates and research-only M10 forecasts are not substituted for missing frozen historical projections.' };
  }
  function usage(p, c) {
    const r = rawStats(p, c); if (!r) return 'Unavailable';
    return ['targets', 'carries', 'receptions', 'receiving_yards', 'rushing_yards', 'passing_yards'].filter(k => n(r[k]) !== null).map(k => `${k.replaceAll('_', ' ')} ${r[k]}`).join(' · ') || 'Unavailable';
  }
  async function readJSON(url, sourceId) {
    const r = window.FIEDataClient?.response ? await window.FIEDataClient.response(url, { sourceId, ttlMs: 60000, persist: false, cache: 'no-store' }) : await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  }
  function loadNFL(force = false) {
    if (!nflPromise || force) nflPromise = readJSON('https://api.sleeper.app/v1/state/nfl', 'editorial-weekly-nfl-state').then(v => { nfl = v; return v; }).catch(() => { nflPromise = null; return null; });
    return nflPromise;
  }
  function matchups(c, force = false) {
    const key = `${c.leagueId}|${c.season}|${c.week}`, old = cache.get(key);
    if (old && !force && Date.now() - old.at < 60000) return old;
    const record = { at: Date.now(), rows: null, error: null };
    cache.set(key, record);
    record.promise = readJSON(`https://api.sleeper.app/v1/league/${encodeURIComponent(c.leagueId)}/matchups/${c.week}`, 'editorial-weekly-matchups').then(rows => {
      if (!Array.isArray(rows)) throw new Error('Invalid matchup response');
      record.rows = rows;
    }).catch(e => { record.error = String(e.message || e); });
    return record;
  }
  function disclosure(title, text, content) {
    const d = node('details', 'fie-weekly-details'), s = node('summary', '', `${title} · ${text}`); d.append(s);
    d.addEventListener('toggle', () => { if (d.open && !d.dataset.built) { d.dataset.built = '1'; const body = content(); if (body) d.append(body); } });
    return d;
  }
  function note(text, tone = 'warning') { const p = node('p', 'fie-weekly-notice', text); p.dataset.tone = tone; return p; }
  function metric(label, value) { const d = node('div', 'fie-weekly-metric'); d.append(node('span', '', label), node('strong', '', value)); return d; }
  function resultBand(c, rows, state) {
    const { mine, opponent, multiple } = pairing(rows, c.rosterId), minePts = n(mine?.points), oppPts = n(opponent?.points);
    const band = node('section', 'fie-weekly-result');
    const fp = window.formatProfile?.() || {};
    const text = fp.chopped ? 'League scoring / survival context' : state === 'completed' ? 'Reported matchup result' : 'Matchup points so far';
    band.append(node('h2', '', text));
    const grid = node('div', 'fie-weekly-metrics'); grid.append(metric(rosterName(c.rosterId), pts(minePts)));
    if (fp.chopped) {
      const valid = rows.filter(r => n(r.points) !== null).sort((a, b) => b.points - a.points);
      const rank = valid.findIndex(r => String(r.roster_id) === c.rosterId);
      grid.append(metric('Observed scoring rank', rank < 0 ? 'Unavailable' : `${rank + 1} / ${valid.length}`), metric('Survival / elimination', 'Unverified'));
      band.append(grid, note('Score rank is context only. The active-team set, cutoff and elimination rules must be verified before declaring survival.'));
    } else {
      grid.append(metric(opponent ? rosterName(opponent.roster_id) : 'Opponent', pts(oppPts)), metric(state === 'completed' ? 'Result' : 'Current margin', minePts === null || oppPts === null ? 'Unavailable' : state === 'completed' ? `${minePts > oppPts ? 'Win' : minePts < oppPts ? 'Loss' : 'Tie'} · ${signed(minePts - oppPts)}` : signed(minePts - oppPts)));
      band.append(grid);
      if (!opponent) band.append(note(multiple ? 'Multiple matching opponent rows; no head-to-head result inferred.' : 'No head-to-head opponent returned for this roster/week.'));
    }
    if (n(mine?.custom_points) !== null) band.append(note(`Commissioner custom_points reported: ${pts(mine.custom_points)}. Matchup total stays as reported; player sums may differ.`));
    return band;
  }
  function resultTable(title, xs, c, state) {
    return window.FIEEditorial.createTable({ title, description: state === 'completed' ? 'Basic · reported player points. Expand for scoring and forecast coverage.' : 'Basic · reported actual points and schedule state. Pregame forecasts stay separate.', caption: contextText(c),
      columns: [{ key: 'slot', label: 'Slot' }, { key: 'name', label: 'Player' }, { key: 'actual', label: 'Actual pts', numeric: true }, ...(state !== 'completed' ? [{ key: 'game', label: 'Game state' }] : [])], rows: xs.map(x => performanceRow(x, c)) });
  }
  function lineupReview(c, mine) {
    const body = node('div');
    body.append(window.FIEEditorial.createTable({ title: 'Lineup comparisons', caption: contextText(c), description: 'Projected totals and realized totals have different meanings. Each alternative needs its own capture and legal roster.',
      columns: [{ key: 'name', label: 'Lineup' }, { key: 'forecast', label: 'Pregame projected pts', numeric: true }, { key: 'actual', label: 'Realized pts', numeric: true }],
      rows: [
        { name: 'Submitted / reported contribution', forecast: null, actual: pts(n(mine?.points)), expanded: [['Total source', 'Reported Sleeper matchup total'], ['Pregame projection', forecastAvailability()]], advanced: [['Roster IDs', (mine?.starters || []).join(', ')], ['Authority', 'Reported outcome; not reconstructed forecast']] },
        ...['FIE projected-best', 'Sleeper projected-best', 'Hindsight legal best'].map(name => ({ name, forecast: null, actual: null, expanded: [['Status', name.startsWith('Hindsight') ? 'Unavailable · no verified historical eligible roster/rule/lock snapshot served' : forecastAvailability()]], advanced: [['Required inputs', 'Frozen eligible roster, historical slots/rules, locks/exclusions and complete compatible player scores'], ['Owner', 'Canonical exact slot optimizer; no greedy replacement or current roster substitution'], ['Scope', 'Full lineup including K/D/ST/IDP where rostered; offensive-only research cannot stand in for it']] }))
      ] })); return body;
  }
  function results(host, c, rows, state, lens = null) {
    const pair = pairing(rows, c.rosterId), mine = pair.mine;
    if (!mine) { host.append(note('No matchup record returned for this roster and selected week.')); return; }
    host.append(resultBand(c, rows, state));
    let xs = reportedPlayers(mine);
    if (lens) xs = xs.filter(x => window.FIECore?.PositionRegistry?.canonical?.(x.position) === lens);
    const fp = window.formatProfile?.() || {};
    host.append(resultTable(lens === 'DEF' ? 'Reported D/ST points' : lens === 'K' ? 'Reported kicker points' : fp.bestBall ? 'Reported automatic contribution' : 'Submitted lineup', xs, c, state));
    if (!xs.length) host.append(note(lens ? `No reported ${lens} starter found. Missing position identity is not assumed to be this position.` : 'Submitted player list unavailable.'));
    const sum = xs.length && xs.every(x => x.actual !== null) ? xs.reduce((a, x) => a + x.actual, 0) : null;
    if(state==='live'){
      const notStarted=xs.filter(x=>gameState(x.p,c).startsWith('Not started')).length,unverified=xs.filter(x=>gameState(x.p,c).includes('unverified')||gameState(x.p,c).includes('unavailable')).length;
      host.append(note(`${notStarted} submitted players verified not started; ${unverified} game states unverified. Started is not the same as finished; a remaining-points forecast is unavailable without compatible live evidence.`,'context'));
    }
    if (!lens && sum !== null && n(mine.points) !== null && Math.abs(sum - mine.points) > .011) host.append(note(`Player sum ${pts(sum)} differs from reported total ${pts(mine.points)}. Corrections, custom points or provider scoring may account for the difference.`));
    const starterSet = new Set((mine.starters || []).map(String));
    const bench = (mine.players || []).filter(id => !starterSet.has(String(id))).map(id => { const p = player(id); return { id: String(id), slot: 'BENCH', name: p?.name || `Player ${id}`, p, actual: n(mine.players_points?.[id]), position: p?.position }; }).filter(x => !lens || window.FIECore?.PositionRegistry?.canonical?.(x.position) === lens);
    host.append(disclosure('Bench', `${bench.length} reported players`, () => resultTable('Reported bench', bench, c, state)));
    host.append(disclosure('Lineup review', 'alternative scores require compatible captures', () => lineupReview(c, mine)));
    host.append(disclosure('Other league scores', `${rows.length} roster records`, () => window.FIEEditorial.createTable({ title: 'League reported scores', caption: contextText(c), columns: [{ key: 'name', label: 'Roster' }, { key: 'actual', label: 'Reported pts', numeric: true }], rows: rows.filter(r => String(r.roster_id) !== c.rosterId).map(r => ({ name: rosterName(r.roster_id), actual: pts(n(r.points)), expanded: [['Players', reportedPlayers(r).map(x => `${x.name}: ${pts(x.actual)}`).join('; ')]], advanced: [['Provider roster ID', String(r.roster_id)], ['Matchup ID', String(r.matchup_id ?? 'Unavailable')], ['Source', 'Sleeper matchup response']] })) })));
  }
  function upcoming(host, c) {
    const fp = window.formatProfile?.() || {}, binding=S().projectionStatus?.weeklyContext;
    const bound=binding?.leagueId===c.leagueId&&Number(binding?.season)===c.season&&Number(binding?.week)===c.week&&S().projectionStatus?.weekly===true;
    if(!bound){
      host.append(node('h2','','Upcoming lineup'),note('Selected-week forecasts unavailable. Refresh weekly context to bind forecasts to this league, season and week. Older player projections are not reused.'));
      const r=(S().rosters||[]).find(r=>String(r.roster_id)===c.rosterId),ids=r?.starters||r?.players||[];
      host.append(window.FIEEditorial.createTable({title:fp.bestBall?'Projected contributors':'Projected starters',caption:contextText(c),description:'Roster context only · forecasts and a recommended lineup are unavailable until this selected week is loaded.',columns:[{key:'name',label:'Roster player'},{key:'forecast',label:'Projected pts',numeric:true}],rows:ids.map(id=>({name:player(id)?.name||`Player ${id}`,forecast:null,expanded:[['Forecast status','Selected-period forecast not loaded']],advanced:[['Source','Current roster context; not a projected selection']]}))}));return;
    }
    const ws = window.FIEUX93?.weeklyDecisionState?.();
    if (!ws?.pool?.length) { host.append(note('No canonical league-legal roster players available. Load the league and weekly context.')); return; }
    const opt = ws.chosen, assignments = opt.assignment || [], ids = new Set(assignments.map(a => a.player));
    const ready = S().weekly?.loaded === true && Number(S().weekly.week) === c.week;
    host.append(node('h2', '', fp.bestBall ? 'Automatic scoring · projected contribution' : 'Projected lineup'));
    if (!ready) host.append(note('Weekly context is not loaded for this selection. Values below use the existing labelled browser estimates; refresh weekly context before relying on them.'));
    if (fp.bestBall) host.append(note('Best Ball chooses scoring contributors automatically. This table is a projected contribution view, not a start/sit instruction.', 'context'));
    const cards = node('div', 'fie-weekly-metrics');
    cards.append(metric('Selected projected total', assignments.length ? pts(opt.total) : 'Unavailable'), metric('Objective', window.FIEUX93?.weeklyMode==='win'?'Existing opponent simulation':'Max expected points'), metric('Lineup coverage', `${assignments.length} / ${starterSlots().length} slots`)); host.append(cards);
    if (opt.unfilledSlots?.length) host.append(note(`Unfilled slots: ${opt.unfilledSlots.join(', ')}. Total is partial.`));
    const toRow = (p, slot, value) => {
      const projection = window.FIEProjectionResolver?.week?.(p, { season: c.season, week: c.week }) || {};
      const rg = window.FIEProjectionResolver?.range?.(p) || {}, id = p.sleeperId || p.player_id;
      return { title: p.name, slot, name: p.name, forecast: `${pts(value)}${projection.estimate ? ' · estimate' : projection.source === 'Sleeper weekly' ? ' · Sleeper' : ''}`, status: p.injuryStatus || p.sleeperStatus || 'No flag reported', context: contextText(c),
        expanded: [['Forecast source', `${projection.source || 'Browser estimate'} · ${projection.confidence || 'unverified'}`], ['Opponent', window.FIEProjectionResolver?.opponent?.(p) || 'Unavailable'], ['Low / high', `${pts(rg.low)} / ${pts(rg.high)} · ${rg.source || 'unavailable'}`], ['Matchup driver', n(p.matchupAdjustment) === null ? null : String(p.matchupAdjustment)], ['Bench slot alternatives', ws.pool.filter(q => q !== p && !ids.has(q) && window.FIECore?.PositionRegistry?.eligible?.(q.position, slot)).map(q => ({q, v: window.FIEProjectionResolver?.week?.(q)?.value})).filter(x => n(x.v) !== null).sort((a,b) => b.v-a.v).slice(0,3).map(x => `${x.q.name}: ${pts(x.v)} (${signed(x.v-value)} vs this slot)`).join('; ') || 'Unavailable'], ['Alternative scope', 'Individual slot comparison; not a complete legal lineup substitution or live transaction'], ['Game / lock context', gameState(p, c)]],
        advanced: [['Player ID', String(id || 'Unavailable')], ['Optimizer', 'Existing FIEUX93 weeklyDecisionState; canonical exact assignment'], ['Objective', 'Existing authorized browser max expected points; season VOR excluded'], ['Source / confidence', `${projection.source || 'Unavailable'} / ${projection.confidence || 'Unavailable'}`], ['Range type', rg.calibrated ? 'Empirical' : 'Estimate'], ['Locks', 'This preview does not infer verified player locks. After kickoff it displays reported submissions instead.'], ['Capture', 'Current browser estimate; not an immutable pregame research capture']] };
    };
    host.append(window.FIEEditorial.createTable({ title: fp.bestBall ? 'Projected contributors' : 'Projected starters', caption: contextText(c), columns: [{ key: 'slot', label: 'Slot' }, { key: 'name', label: 'Player' }, { key: 'forecast', label: 'Projected pts', numeric: true }, { key: 'status', label: 'Status' }], rows: assignments.map(a => toRow(a.player, a.slot, a.value)) }));
    const bench = ws.pool.filter(p => !ids.has(p));
    host.append(disclosure('Bench / contingencies', `${bench.length} players`, () => window.FIEEditorial.createTable({ title: 'Bench forecasts', caption: contextText(c), columns: [{ key: 'name', label: 'Player' }, { key: 'forecast', label: 'Projected pts', numeric: true }, { key: 'status', label: 'Status' }], rows: bench.map(p => toRow(p, 'BENCH', window.FIEProjectionResolver?.week?.(p)?.value)) })));
    host.append(disclosure('Lineup objective', 'max points / existing opponent-aware mode', () => {
      const d=node('div');d.append(note('These are the existing browser objectives. Opponent-aware mode is a simulation estimate and remains separate from prospective validation.','context'));
      for(const [mode,label] of [['points','Max expected points'],['win','Max win probability']]){const b=node('button','',label);b.type='button';b.onclick=()=>window.FIEUX93?.setWeeklyMode?.(mode);d.append(b);}return d;
    }));
    host.append(disclosure('Opponent / simulation', 'existing supported model, on demand', () => {
      const d = node('div'); d.append(note('Use Matchup & Playoffs for the existing simulation and its assumptions. This view does not manufacture a new win probability.', 'context'));
      const b = node('button', '', 'Open Matchup & Playoffs'); b.type = 'button'; b.onclick = () => window.activateTab?.('matchupsim'); d.append(b); return d;
    }));
  }
  function root() {
    let e = $('fieWeeklyWorkspace');
    if (!e) { e = node('div', 'fie-weekly-workspace'); e.id = 'fieWeeklyWorkspace'; $('mainArea')?.prepend(e); }
    return e;
  }
  function render() {
    const host = root(); if (!host) return;
    document.body.classList.add('fie-weekly-active');
    $('fie93WeeklyPanel')?.classList.add('hidden');
    host.hidden = false; host.replaceChildren();
    const c = scope(), key = keyFor(c); activeKey = key;
    if (!c.leagueId || !c.rosterId) { host.append(node('h2', '', 'Weekly'), note('Load a league and select a roster to see matchup results or upcoming projections.')); return; }
    if (Number(S().league?.season) !== c.season) { host.append(note('Selected season does not match the loaded league. Load that season’s league before requesting its matchups.')); return; }
    const state = period(c);
    const controls=$('weeklyControls');
    let sources=$('fieWeeklySources');
    if(controls&&!sources){sources=node('details');sources.id='fieWeeklySources';sources.append(node('summary','','Forecast sources & tools'));controls.append(sources);if($('weeklyStatus'))sources.append($('weeklyStatus'));}
    if(sources){if(state==='upcoming')controls.append(sources);else if($('fieDataCoverage'))$('fieDataCoverage').append(sources);}
    if(sources&&$('weeklyLoadBtn')){if(state==='upcoming')controls.insertBefore($('weeklyLoadBtn'),sources);else sources.append($('weeklyLoadBtn'));}
    const header = node('div', 'fie-weekly-heading'); header.append(node('p', 'fie-level', state === 'completed' ? 'Completed week · reported results' : state === 'upcoming' ? 'Upcoming week' : state === 'live' ? 'Live / started week' : 'Week status unverified'));
    const refresh = node('button', '', 'Refresh results'); refresh.type = 'button'; refresh.onclick = () => refreshData(true); header.append(refresh); host.append(header);
    const record = matchups(c);
    if (state === 'upcoming') upcoming(host, c);
    else if (record.rows) {
      if (state === 'unknown') host.append(note('Week timing cannot be verified. These are reported actuals; no final outcome or forecast is inferred.'));
      results(host, c, record.rows, state);
    } else host.append(note(record.error ? `Matchup results unavailable: ${record.error}. Use Refresh results to retry.` : 'Loading reported matchup results…'));
    if (state === 'upcoming' && record.error) host.append(note(`Matchup schedule unavailable: ${record.error}`));
    host.append(disclosure('Data coverage', 'sources, missing evidence and scoring scope', () => {
      const d = node('div'); d.append(note('Reported actual points are available from matchup records. Detailed scoring requires loaded raw stats. Historical forecast errors and alternative lineup scores require compatible served immutable captures; missing evidence is shown as unavailable.', 'context'));
      const b = node('button', '', 'Advanced week evidence'); b.type = 'button'; b.onclick = () => window.FIEEditorial.openReader({ title: 'Weekly evidence coverage', context: contextText(c), entries: [['Week state', state], ['Result fetched', new Date(record.at).toISOString()], ['Result source', `Sleeper league ${c.leagueId}/matchups/${c.week}`], ['NFL timing source', nfl ? 'Sleeper state/nfl + loaded nflverse schedule' : 'Unavailable; schedule only'], ['Historical forecast', forecastAvailability()], ['Historical legal alternatives', 'Unavailable unless archived eligibility/rules/locks and complete scores are served'], ['Scoring', 'Canonical ruleValue via read-only weeklyScoringBreakdown; unsupported inputs stay null'], ['Research authority', 'M9 champion and all existing gates unchanged; M10 not promoted']] }, b); d.append(b); return d;
    }));
    const version = ++serial;
    if (!record.rows && !record.error) record.promise.then(() => { if (version === serial && key === keyFor(scope()) && S().activeTab === 'startsit') render(); });
    if (!nfl) loadNFL().then(v => { if (v && key === keyFor(scope()) && S().activeTab === 'startsit') render(); });
  }
  function refreshData(force = false) { const c = scope(); cache.delete(`${c.leagueId}|${c.season}|${c.week}`); loadNFL(force); render(); }
  function specialist({ host, kind, week, setWeek, rerender, rows, action, next3, replacement }) {
    if (!host || !S().league) return false;
    const c = { ...scope(), week: Number(week) }, state = period(c), expected = kind === 'DEF' ? 'dst' : 'kicker';
    // Preserve specialist owners' loading behavior until their existing board is available.
    if (state === 'upcoming' && !rows?.length) return false;
    host.replaceChildren(); host.classList.add('fie-weekly-workspace');
    const label = node('label', '', 'Selected week '), select = node('select');
    select.setAttribute('aria-label', kind === 'DEF' ? 'D/ST week' : 'Kicker week');
    for (let w = 1; w <= 18; w++) { const o = node('option', '', `Week ${w}`); o.value = String(w); select.append(o); }
    select.value = String(c.week); select.onchange = () => { window.FIEEditorial?.clearDisclosures(); setWeek(Number(select.value)); rerender(); };
    label.append(select); host.append(label, node('p', 'fie-level', state === 'completed' ? 'Completed week · reported specialist actuals' : state === 'upcoming' ? 'Upcoming specialist forecasts' : 'Reported specialist actuals · timing may be unverified'));
    if (state !== 'upcoming') {
      const r = matchups(c);
      if (r.rows) results(host, c, r.rows, state, kind);
      else host.append(note(r.error ? `Specialist results unavailable: ${r.error}` : 'Loading reported specialist points…'));
      if (!r.rows && !r.error) r.promise.then(() => { if (S().activeTab === expected) rerender(); });
    } else {
      const mine = rows.find(x => x.status === 'Yours'), best = rows.find(x => x.status === 'FA');
      const band = node('div', 'fie-weekly-metrics'); band.append(metric('Rostered', mine ? `${mine.name || mine.team} · ${pts(mine.mean)}` : 'None found'), metric('Best available forecast', best ? `${best.name || best.team} · ${pts(best.mean)}` : 'Unavailable')); host.append(band);
      host.append(window.FIEEditorial.createTable({ title: kind === 'DEF' ? 'D/ST outlook' : 'Kicker outlook', caption: contextText(c), description: 'Basic · rank, weekly forecast and current owner action. Expand for ranges, schedule and model context.',
        columns: [{ key: 'name', label: kind === 'DEF' ? 'D/ST' : 'Kicker' }, { key: 'rank', label: 'Rank', numeric: true }, { key: 'forecast', label: 'Projected pts', numeric: true }, { key: 'action', label: 'State' }],
        rows: rows.map(x => ({ title: x.name || x.team, name: x.name || x.team, rank: x.rank, forecast: `${pts(x.mean)}${x.estimate ? ' · estimate' : ''}`, action: action(x), context: contextText(c),
          expanded: [['Ownership', x.status], ['Opponent', x.opp], ['Low / high', `${pts(x.low)} / ${pts(x.high)}${x.estimate ? ' · estimate' : ''}`], ['Vs replacement', n(replacement?.mean) === null || n(x.mean) === null ? null : signed(x.mean - replacement.mean)], ['Next 3 weekly mean', pts(next3(x))], ['Source', x.source], ['Scope', x.estimate ? 'Baseline / future-week estimate' : x.active ? 'Governed current' : 'Baseline']],
          advanced: [['Existing model owner', kind === 'DEF' ? 'FIEDST' : 'FIEKicker'], ['Player / team ID', String(x.id || x.team)], ['Selected period', `${c.season} / ${c.week}`], ['Scoring', 'Loaded league settings; existing specialist owner computes the board'], ['Capture', 'Current board; not frozen historical evidence'], ['Status', x.status], ['Source', x.source], ['Model evidence', 'Existing specialist drawer retains full model drivers and Weeks 1–18 series; open from the specialist detail below.']] })) }));
      host.append(disclosure('Specialist model detail', 'original drivers and Weeks 1–18 series', () => {
        const d = node('div');
        const sel = node('select'); sel.setAttribute('aria-label', 'Specialist player detail');
        rows.forEach((x,i) => { const o = node('option','', x.name || x.team); o.value=String(i); sel.append(o); });
        const b = node('button','','Open full specialist detail'); b.type='button'; b.onclick=()=> (kind==='DEF'?window.FIEDST:window.FIEKicker)?.openDrawer?.(rows[Number(sel.value)]);
        d.append(sel,b); return d;
      }));
    }
    if (!nfl) loadNFL().then(v => { if (v && S().activeTab === expected) rerender(); });
    return true;
  }
  function sync() {
    const on = S().activeTab === 'startsit' && !S().portfolioMode;
    document.body.classList.toggle('fie-weekly-active', on);
    if ($('fieWeeklyWorkspace')) $('fieWeeklyWorkspace').hidden = !on;
    if (on && activeKey !== keyFor(scope())) render();
  }
  window.FIEWeeklyWorkspace = Object.freeze({ VERSION: 'editorial-p02', render, specialist, refresh: refreshData, period, kickoff, pairing, reportedPlayers, scoring, forecastAvailability });
  window.addEventListener('fie:league-changing', () => { ++serial; activeKey = ''; cache.clear(); window.FIEEditorial?.clearDisclosures(); $('fieWeeklyWorkspace')?.replaceChildren(); });
  window.addEventListener('fie:league-loaded', () => { activeKey = ''; sync(); });
  document.addEventListener('change', e => { if (['seasonSelect', 'weekSelect', 'weeklyRosterPicker'].includes(e.target?.id)) { window.FIEEditorial?.clearDisclosures(); activeKey = ''; clearTimeout(timer); timer = setTimeout(sync, 0); } });
  const bind = () => {
    const observed = $('mainArea');
    if (observed) new MutationObserver(() => { clearTimeout(timer); timer = setTimeout(sync, 0); }).observe(observed, { attributes: true, attributeFilter: ['class'] });
    const nav = $('sectionTitle'); if (nav) new MutationObserver(sync).observe(nav, { childList: true });
    sync();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind); else bind();
})();
