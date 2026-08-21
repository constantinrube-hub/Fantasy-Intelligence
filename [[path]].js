const NFLVERSE = {
  "players": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv",
    ttl: 86400
  },
  "contracts": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv",
    ttl: 86400
  },
  "stats-regpost-2025": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_regpost_2025.csv",
    ttl: 21600
  },
  "snaps-2025": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2025.csv",
    ttl: 86400
  },
  "schedule": {
    url: "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv",
    ttl: 21600
  },
  "weekly-2025": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2025.csv",
    ttl: 86400
  },
  "weekly-2026": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.csv",
    ttl: 3600
  },
  "snaps-2026": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2026.csv",
    ttl: 3600
  },
  "depth-2026": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_2026.csv",
    ttl: 3600
  },
  "team-2025": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/stats_team/stats_team_week_2025.csv",
    ttl: 86400
  },
  "team-2026": {
    url: "https://github.com/nflverse/nflverse-data/releases/download/stats_team/stats_team_week_2026.csv",
    ttl: 3600
  }
};

function resolveRoute(parts) {
  if (parts[0] === "nflverse" && parts.length === 2 && NFLVERSE[parts[1]]) {
    const item = NFLVERSE[parts[1]];
    return { ...item, source: `nflverse:${parts[1]}` };
  }

  if (parts[0] === "sleeper" && parts[1] === "players" && parts.length === 2) {
    return {
      url: "https://api.sleeper.app/v1/players/nfl?active=true",
      ttl: 86400,
      source: "sleeper:players"
    };
  }

  if (parts[0] === "sleeper" && parts[1] === "projections") {
    const season = String(parts[2] || "");
    const week = parts[3] == null ? null : String(parts[3]);
    if (!/^20\d{2}$/.test(season)) return null;
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
  headers.set("Cache-Control", `public, max-age=60, s-maxage=${meta.ttl}`);
  headers.set("X-FIE-Cache", cacheStatus);
  headers.set("X-FIE-Source", meta.source);
  if (!headers.has("X-FIE-Fetched-At")) {
    headers.set("X-FIE-Fetched-At", new Date().toISOString());
  }
  headers.delete("set-cookie");
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers
  });
}

export async function onRequestGet(context) {
  const raw = context.params.path;
  const parts = Array.isArray(raw) ? raw : raw ? [raw] : [];
  const meta = resolveRoute(parts);
  if (!meta) {
    return Response.json(
      { error: "Unknown or disallowed data route." },
      { status: 404, headers: { "Cache-Control": "no-store" } }
    );
  }

  const cache = caches.default;
  const cacheUrl = new URL(context.request.url);
  const cacheKey = new Request(cacheUrl.toString(), { method: "GET" });

  const cached = await cache.match(cacheKey);
  if (cached) {
    return responseWithMeta(cached, meta, "HIT");
  }

  let upstream;
  try {
    upstream = await fetch(meta.url, {
      redirect: "follow",
      headers: {
        "User-Agent": "Fantasy-Intelligence-Engine-V7/1.0",
        "Accept": "*/*"
      }
    });
  } catch (error) {
    return Response.json(
      { error: "Upstream fetch failed.", source: meta.source, detail: String(error?.message || error) },
      {
        status: 502,
        headers: {
          "Cache-Control": "no-store",
          "X-FIE-Cache": "MISS",
          "X-FIE-Source": meta.source,
          "X-FIE-Fetched-At": new Date().toISOString()
        }
      }
    );
  }

  if (!upstream.ok) {
    const body = await upstream.text().catch(() => "");
    return new Response(body || `Upstream returned ${upstream.status}`, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("Content-Type") || "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
        "X-FIE-Cache": "MISS",
        "X-FIE-Source": meta.source,
        "X-FIE-Fetched-At": new Date().toISOString()
      }
    });
  }

  const headers = new Headers(upstream.headers);
  headers.set("Cache-Control", `public, max-age=60, s-maxage=${meta.ttl}`);
  headers.set("X-FIE-Cache", "MISS");
  headers.set("X-FIE-Source", meta.source);
  headers.set("X-FIE-Fetched-At", new Date().toISOString());
  headers.delete("set-cookie");

  const response = new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers
  });

  context.waitUntil(cache.put(cacheKey, response.clone()));
  return response;
}

export function onRequest(context) {
  if (context.request.method !== "GET") {
    return new Response("Method Not Allowed", {
      status: 405,
      headers: { Allow: "GET" }
    });
  }
  return onRequestGet(context);
}
