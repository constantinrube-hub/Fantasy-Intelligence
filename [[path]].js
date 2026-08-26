import { FIE_RELEASE } from "../../release.js";
const STATIC_NFLVERSE = {
  players: { url: 'https://github.com/nflverse/nflverse-data/releases/download/players/players.csv', ttl: 86400 },
  contracts: { url: 'https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv', ttl: 86400 },
  schedule: { url: 'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv', ttl: 21600 }
};

function validSeason(value) {
  return /^20\d{2}$/.test(String(value || '')) && Number(value) >= 2010 && Number(value) <= 2035;
}

function seasonalNflverse(dataset, season) {
  if (!validSeason(season)) return null;
  const y = String(season);
  const defs = {
    'stats-regpost': [`https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_regpost_${y}.csv`, 21600],
    weekly: [`https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_${y}.csv`, Number(y) >= new Date().getUTCFullYear() ? 3600 : 86400],
    snaps: [`https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_${y}.csv`, Number(y) >= new Date().getUTCFullYear() ? 3600 : 86400],
    depth: [`https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_${y}.csv`, 3600],
    team: [`https://github.com/nflverse/nflverse-data/releases/download/stats_team/stats_team_week_${y}.csv`, Number(y) >= new Date().getUTCFullYear() ? 3600 : 86400]
  };
  const d = defs[dataset];
  return d ? { url: d[0], ttl: d[1], source: `nflverse:${dataset}:${y}` } : null;
}

function resolveRoute(parts) {
  if (parts[0] === 'nflverse') {
    if (parts.length === 2 && STATIC_NFLVERSE[parts[1]]) {
      const item = STATIC_NFLVERSE[parts[1]];
      return { ...item, source: `nflverse:${parts[1]}` };
    }

    // V8.9 canonical season-aware routes.
    if (parts.length === 3) {
      const seasonal = seasonalNflverse(parts[1], parts[2]);
      if (seasonal) return seasonal;
    }

    // Backward-compatible V7/V8 aliases. These remain allowlisted only.
    const legacy = String(parts[1] || '').match(/^(stats-regpost|weekly|snaps|depth|team)-(20\d{2})$/);
    if (parts.length === 2 && legacy) {
      const seasonal = seasonalNflverse(legacy[1], legacy[2]);
      if (seasonal) return seasonal;
    }
  }

  if (parts[0] === 'sleeper' && parts[1] === 'players' && parts.length === 2) {
    return { url: 'https://api.sleeper.app/v1/players/nfl?active=true', ttl: 86400, source: 'sleeper:players' };
  }

  if (parts[0] === 'sleeper' && parts[1] === 'projections') {
    const season = String(parts[2] || '');
    const week = parts[3] == null ? null : String(parts[3]);
    if (!validSeason(season)) return null;
    if (week !== null && !/^(?:[1-9]|1[0-8])$/.test(week)) return null;
    const suffix = week ? `${season}/${week}` : season;
    return {
      url: `https://api.sleeper.com/projections/nfl/${suffix}?season_type=regular`,
      ttl: week ? 900 : 3600,
      source: week ? `sleeper:weekly-projections:${season}:${week}` : `sleeper:season-projections:${season}`
    };
  }

  return null;
}

function responseWithMeta(response, meta, cacheStatus) {
  const headers = new Headers(response.headers);
  headers.set('Cache-Control', `public, max-age=60, s-maxage=${meta.ttl}`);
  headers.set('X-FIE-Cache', cacheStatus);
  headers.set('X-FIE-Source', meta.source);
  if (!headers.has('X-FIE-Fetched-At')) headers.set('X-FIE-Fetched-At', new Date().toISOString());
  headers.set('X-FIE-Release', FIE_RELEASE.release);
  headers.delete('set-cookie');
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

export async function onRequestGet(context) {
  const raw = context.params.path;
  const parts = Array.isArray(raw) ? raw : raw ? [raw] : [];
  const meta = resolveRoute(parts);
  if (!meta) {
    return Response.json({ error: 'Unknown or disallowed data route.' }, { status: 404, headers: { 'Cache-Control': 'no-store' } });
  }

  const cache = caches.default;
  const cacheUrl = new URL(context.request.url);
  const cacheKey = new Request(cacheUrl.toString(), { method: 'GET' });
  const cached = await cache.match(cacheKey);
  if (cached) return responseWithMeta(cached, meta, 'HIT');

  let upstream;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort('upstream timeout'), 20000);
  try {
    upstream = await fetch(meta.url, {
      redirect: 'follow', signal: controller.signal,
      headers: { 'User-Agent': `Fantasy-Intelligence-Engine/${FIE_RELEASE.release}`, Accept: '*/*' }
    });
  } catch (error) {
    return Response.json(
      { error: 'Upstream fetch failed.', source: meta.source, detail: String(error?.message || error) },
      { status: 502, headers: { 'Cache-Control': 'no-store', 'X-FIE-Cache': 'MISS', 'X-FIE-Source': meta.source, 'X-FIE-Release': FIE_RELEASE.release, 'X-FIE-Fetched-At': new Date().toISOString() } }
    );
  } finally { clearTimeout(timeout); }

  if (!upstream.ok) {
    return Response.json({error:`Upstream returned ${upstream.status}.`,source:meta.source},{
      status: upstream.status,
      headers: { 'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-FIE-Cache':'MISS','X-FIE-Source':meta.source,'X-FIE-Release':FIE_RELEASE.release,'X-FIE-Fetched-At':new Date().toISOString()}
    });
  }

  const headers = new Headers(upstream.headers);
  headers.set('Cache-Control', `public, max-age=60, s-maxage=${meta.ttl}`);
  headers.set('X-FIE-Cache', 'MISS');
  headers.set('X-FIE-Source', meta.source);
  headers.set('X-FIE-Fetched-At', new Date().toISOString());
  headers.set('X-FIE-Release', FIE_RELEASE.release);
  headers.delete('set-cookie');
  const response = new Response(upstream.body, { status: upstream.status, statusText: upstream.statusText, headers });
  context.waitUntil(cache.put(cacheKey, response.clone()));
  return response;
}

export function onRequest(context) {
  if (context.request.method !== 'GET') return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'GET' } });
  return onRequestGet(context);
}
