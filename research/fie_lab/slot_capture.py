#!/usr/bin/env python3
"""
slot_capture.py: decision snapshot for ONE kickoff slot, about 75 minutes before its first kickoff.

Author: Claude (for Constantin), 30 Oct 2026 (readiness item c4). Python 3.9+ standard library only.
Runs on your PC (Task Scheduler entries come from slot_schedule.py). Writes nothing to the FIE repo.
The Odds API key is read from ODDS_API_KEY and never printed or saved.

WHAT ONE RUN SAVES  <out>/slot_<season>_w<WW>_<SLOT>_<UTC timestamp>/
  sleeper_projections_<POS>.json.gz  Sleeper weekly projections per position: QB RB WR TE K DEF DL LB DB
  sleeper_projections_ALL.json.gz    one unfiltered request (cross-check)
  sleeper_players_full.json.gz       full Sleeper player file (injury statuses, depth charts; COMP-S input)
  sleeper_players.json.gz            compact player list incl. IDP, same format as sunday_capture.py v3
  props/event_<id>.json, props/events.json   player props for the slot's games (once per game per week)
  odds_<season>_w<WW>_<ts>.json      game lines (spreads/totals), schema fie-lab-odds-capture-v1,
                                     FILTERED to this NFL week (see bk8: lines.pregame() mislabels next
                                     week's games); the unfiltered response is in raw/ with its hash
  manifest.json                      slot, games, cutoff, every step's status, credits, SHA-256 per file,
                                     aligned props+Sleeper pairs per game (market-variants test), fallbacks
The folder has the sunday_capture.py file names, so the frozen engine's Sunday path can read it:
  py -3 -m fie_lab.weekly_run --week 9 --odds <slot>\\odds_....json --sunday <slot folder>
That is how "FIE = frozen Thursday means x availability on the slot's statuses" is computed: by the
frozen engine, not by a second copy of the F1 rules in this script.

CREDITS (The Odds API, 500/month on the free plan)
  props: (markets returned) per game, once per game per week (a game captured by an earlier slot of the
         same week is skipped); never below --reserve remaining (default per week: W9 300, W10 200,
         W11 100, W12 5, otherwise 60).
  lines: 2 per slot (--no-lines to skip). The events list is free.

RUN (PowerShell)
  py -3 slot_capture.py --week 9 --slot next --out C:\\Users\\User\\FIE\\FIE-Lab\\slots
  py -3 slot_capture.py --week 9 --slot-kickoff 2026-11-08T18:00:00Z --out ...   (what the tasks run)
  --dry-run lists the slot, its games and the maximum cost, buys nothing, writes nothing.
  --no-props / --no-lines / --markets a,b,c / --reserve N to override.

EXIT CODES  0 = every requested step OK; 3 = finished with at least one failed or late step (see the
            manifest); 2 = usage/setup error. A failed step never stops the other steps.

CHANGE LOG
  v1 (30 Oct 2026): first version.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = "1"
SLEEPER_HOSTS = ["https://api.sleeper.app", "https://api.sleeper.com"]
ODDS_BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB"]
KEEP = {"QB", "RB", "WR", "TE", "K", "DL", "LB", "DB", "DE", "DT", "CB", "S", "ILB", "OLB", "EDGE", "IDL"}
CORE_MARKETS = ["player_pass_yds", "player_pass_tds", "player_rush_yds", "player_receptions",
                "player_reception_yds", "player_anytime_td", "player_kicking_points"]
RESERVE_BY_WEEK = {9: 300, 10: 200, 11: 100, 12: 5}
SLOT_GAP = timedelta(minutes=45)     # games kicking off within 45 min of the slot's first game share the slot
CUTOFF_LEAD = timedelta(minutes=75)  # target cutoff T-75 (after inactives at ~T-90)

# ---------------------------------------------------------------- HTTP (replaceable in tests)


def http_get(url: str, timeout: int = 120) -> tuple[int, bytes, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": f"fie-lab-slot-capture/{VERSION}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        return e.code, e.read(), {k.lower(): v for k, v in (e.headers or {}).items()}


def sleeper_get(path: str) -> tuple[bytes, str]:
    last = None
    for host in SLEEPER_HOSTS:
        try:
            status, body, _ = http_get(host + path)
            if status == 200:
                return body, host + path
            last = f"HTTP {status}"
        except Exception as e:  # noqa: BLE001 - try the other host once
            last = e
    raise RuntimeError(f"Sleeper request failed on both hosts for {path}: {last}")


def odds_get(path: str, params: dict) -> tuple[int, object, dict, bytes]:
    status, body, headers = http_get(ODDS_BASE + path + "?" + urllib.parse.urlencode(params), timeout=90)
    try:
        data = json.loads(body)
    except Exception:  # noqa: BLE001
        data = None
    credits = {k: headers.get(k) for k in ("x-requests-last", "x-requests-used", "x-requests-remaining")}
    return status, data, credits, body

# ---------------------------------------------------------------- pure helpers (tested)


def utc(s: str) -> datetime:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)


def iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def week_end(first_kickoff: datetime) -> datetime:
    """End of the NFL week containing first_kickoff: the next Wednesday 12:00 UTC (weeks run Thu-Mon)."""
    d = first_kickoff.astimezone(timezone.utc)
    days = (2 - d.weekday()) % 7
    end = (d + timedelta(days=days)).replace(hour=12, minute=0, second=0, microsecond=0)
    return end if end > d else end + timedelta(days=7)


def slots_from_events(events: list) -> list[dict]:
    """Group events into kickoff slots: a slot opens at a game's kickoff and takes every later game that
    starts within SLOT_GAP of the slot's first kickoff. Label = <weekday>_<HHMM UTC>."""
    evs = sorted((e for e in events if e.get("commence_time")), key=lambda e: e["commence_time"])
    slots: list[dict] = []
    for e in evs:
        k = utc(e["commence_time"])
        if slots and k - slots[-1]["first_kickoff"] < SLOT_GAP:
            slots[-1]["events"].append(e)
        else:
            slots.append({"first_kickoff": k, "events": [e]})
    for s in slots:
        k = s["first_kickoff"]
        s["label"] = f"{k.strftime('%a').upper()}_{k.strftime('%H%M')}Z"
        s["cutoff"] = k - CUTOFF_LEAD
    return slots


def pick_slot(slots: list[dict], now: datetime, slot_kickoff: str | None) -> dict | None:
    if slot_kickoff:
        k = utc(slot_kickoff)
        for s in slots:  # exact first-kickoff match, else a slot whose first game moved by < SLOT_GAP
            if abs(s["first_kickoff"] - k) < SLOT_GAP:
                return s
        return None
    upcoming = [s for s in slots if s["first_kickoff"] > now]
    return upcoming[0] if upcoming else None


def props_already_captured(out_dir: Path, season: int, week: int, current: Path | None = None) -> dict:
    """event_id -> folder name, for games whose props an earlier slot run of this week captured (HTTP 200)."""
    done: dict[str, str] = {}
    for m in sorted(out_dir.glob(f"slot_{season}_w{week:02d}_*/manifest.json")):
        if current is not None and m.parent == current:
            continue
        try:
            man = json.loads(m.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - a broken manifest never blocks a capture
            continue
        for c in (man.get("steps", {}).get("props", {}).get("calls") or []):
            if c.get("status") == 200 and c.get("event_id"):
                done.setdefault(c["event_id"], m.parent.name)
    return done


def previous_ok(out_dir: Path, season: int, week: int, step: str, current: Path) -> str | None:
    """Latest earlier slot folder of this week whose <step> finished OK (the fallback for a failed step)."""
    best = None
    for m in sorted(out_dir.glob(f"slot_{season}_w{week:02d}_*/manifest.json")):
        if m.parent == current:
            continue
        try:
            man = json.loads(m.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if man.get("steps", {}).get(step, {}).get("status") == "OK":
            best = m.parent.name
    return best


def filter_lines(events: list, start: datetime, end: datetime) -> list:
    return [e for e in events if start <= utc(e["commence_time"]) < end]

# ---------------------------------------------------------------- capture steps


def save_gz(path: Path, data: bytes) -> str:
    with gzip.open(path, "wb") as fh:
        fh.write(data)
    return sha256(path.read_bytes())


def step_sleeper(folder: Path, season: int, week: int, files: dict) -> dict:
    counts, requests, warnings = {}, [], []
    for pos in POSITIONS:
        data, url = sleeper_get(f"/projections/nfl/{season}/{week}?season_type=regular&position[]={pos}")
        rows = json.loads(data)
        n = len(rows) if isinstance(rows, list) else 0
        if not n:
            warnings.append(f"no {pos} rows")
        name = f"sleeper_projections_{pos}.json.gz"
        files[name] = save_gz(folder / name, data)
        counts[pos] = n
        requests.append(url)
    try:
        data, url = sleeper_get(f"/projections/nfl/{season}/{week}?season_type=regular")
        files["sleeper_projections_ALL.json.gz"] = save_gz(folder / "sleeper_projections_ALL.json.gz", data)
        rows = json.loads(data)
        counts["ALL"] = len(rows) if isinstance(rows, list) else 0
        requests.append(url)
    except Exception as e:  # noqa: BLE001 - cross-check only
        warnings.append(f"unfiltered projections failed: {e}")
    data, url = sleeper_get("/v1/players/nfl")
    players = json.loads(data)
    files["sleeper_players_full.json.gz"] = save_gz(folder / "sleeper_players_full.json.gz", data)
    compact = {pid: {k: p.get(k) for k in ("full_name", "team", "position", "fantasy_positions", "injury_status",
                                           "injury_body_part", "practice_participation", "status", "gsis_id")}
               for pid, p in players.items()
               if p.get("position") in KEEP or set(p.get("fantasy_positions") or []) & KEEP or pid.isalpha()}
    files["sleeper_players.json.gz"] = save_gz(folder / "sleeper_players.json.gz", json.dumps(compact).encode())
    requests.append(url)
    counts["players_compact"] = len(compact)
    status_counts: dict[str, int] = {}
    for p in compact.values():
        s = p.get("injury_status") or "none"
        status_counts[s] = status_counts.get(s, 0) + 1
    return {"status": "OK", "rows": counts, "injury_status_counts": status_counts,
            "requests": requests, "warnings": warnings}


def step_props(folder: Path, key: str, slot: dict, markets: list, reserve: int, already: dict,
               events_body: bytes, remaining: float, files: dict) -> dict:
    sub = folder / "props"
    sub.mkdir()
    (sub / "events.json").write_bytes(events_body)
    files["props/events.json"] = sha256(events_body)
    calls = []
    for e in slot["events"]:
        game = f"{e.get('away_team')} @ {e.get('home_team')}"
        if e["id"] in already:
            calls.append({"event_id": e["id"], "game": game, "skipped": "ALREADY_CAPTURED_THIS_WEEK",
                          "captured_in": already[e["id"]]})
            continue
        if remaining - len(markets) < reserve:
            calls.append({"event_id": e["id"], "game": game, "skipped": "RESERVE", "remaining": remaining})
            continue
        status, data, credits, body = odds_get(f"/events/{e['id']}/odds", {
            "apiKey": key, "regions": "us", "markets": ",".join(markets), "oddsFormat": "decimal"})
        name = f"props/event_{e['id']}.json"
        (folder / name).write_bytes(body)
        files[name] = sha256(body)
        remaining = float(credits.get("x-requests-remaining") or remaining)
        returned = sorted({m.get("key") for b in (data or {}).get("bookmakers") or [] for m in b.get("markets") or []})
        calls.append({"event_id": e["id"], "game": game, "commence_time": e.get("commence_time"),
                      "status": status, "credits": credits, "markets_returned": returned})
    bought = [c for c in calls if "status" in c]
    failed = [c for c in bought if c["status"] != 200]
    reserve_skips = [c for c in calls if c.get("skipped") == "RESERVE"]
    status = "FAILED" if failed or reserve_skips else ("OK" if bought else "SKIPPED_ALL_CAPTURED")
    return {"status": status, "markets_requested": markets, "reserve": reserve, "calls": calls,
            "remaining_after": remaining}


def step_lines(folder: Path, key: str, season: int, week: int, slot: dict, stamp: str, files: dict) -> dict:
    status, data, credits, body = odds_get("/odds", {"apiKey": key, "regions": "us", "markets": "spreads,totals",
                                                     "oddsFormat": "american", "dateFormat": "iso"})
    raw = folder / "raw"
    raw.mkdir(exist_ok=True)
    raw_name = f"raw/odds_unfiltered_{stamp}.json"
    (folder / raw_name).write_bytes(body)
    files[raw_name] = sha256(body)
    if status != 200 or not isinstance(data, list):
        return {"status": "FAILED", "http_status": status, "credits": credits}
    end = week_end(slot["first_kickoff"])
    start = end - timedelta(days=7)
    kept = filter_lines(data, start, end)
    record = {"schema": "fie-lab-odds-capture-v1", "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "season": season, "week": week,
              "request": {"url": ODDS_BASE + "/odds", "regions": "us", "markets": "spreads,totals"},
              "credits": {"remaining": credits.get("x-requests-remaining"), "used": credits.get("x-requests-used"),
                          "last": credits.get("x-requests-last")},
              "response": kept,
              "fie_lab_filter": {"rule": "commence_time in [week_end - 7 d, week_end), week_end = next Wed 12:00 UTC",
                                 "window_utc": [iso(start), iso(end)], "source_file": raw_name,
                                 "source_sha256": files[raw_name], "games_in_source": len(data), "games_kept": len(kept)}}
    name = f"odds_{season}_w{week:02d}_{stamp}.json"
    (folder / name).write_text(json.dumps(record, indent=1), encoding="utf-8")
    files[name] = sha256((folder / name).read_bytes())
    return {"status": "OK", "file": name, "games_kept": len(kept), "games_in_source": len(data), "credits": credits}

# ---------------------------------------------------------------- main


def aligned_pairs(slot: dict, props: dict, sleeper_ok: bool, this_folder: str) -> list[dict]:
    """Per game: is there a props snapshot from THIS run next to this run's Sleeper snapshot? (registration
    market_variants_registration_v1.json: unaligned games are dropped, never filled from another cutoff)."""
    by_id = {c["event_id"]: c for c in props.get("calls", [])}
    out = []
    for e in slot["events"]:
        c = by_id.get(e["id"], {})
        same_run = c.get("status") == 200
        out.append({"event_id": e["id"], "game": f"{e.get('away_team')} @ {e.get('home_team')}",
                    "aligned": bool(same_run and sleeper_ok),
                    "props_from": this_folder if same_run else c.get("captured_in"),
                    "reason": None if same_run and sleeper_ok else
                    ("SLEEPER_FAILED" if not sleeper_ok else c.get("skipped") or f"HTTP_{c.get('status')}")})
    return out


def run(a, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    key = os.environ.get("ODDS_API_KEY")
    events, events_body, remaining = [], b"[]", 0.0
    if key:
        st, data, credits, body = odds_get("/events", {"apiKey": key})   # free
        if st == 200 and isinstance(data, list):
            events, events_body = data, body
            remaining = float(credits.get("x-requests-remaining") or 0)
        else:
            print(f"/events failed: HTTP {st}; continuing Sleeper-only if --slot-kickoff was given", file=sys.stderr)
    if not events:
        # Without the events list the slot's games are unknown: props and lines are impossible, but the
        # Sleeper half (projections + statuses) is still worth having. Needs an explicit --slot-kickoff.
        if not a.slot_kickoff:
            print("no events list (no ODDS_API_KEY or /events failed): pass --slot-kickoff for a Sleeper-only run",
                  file=sys.stderr)
            return 2
        k = utc(a.slot_kickoff)
        slot = {"first_kickoff": k, "events": [], "label": f"{k.strftime('%a').upper()}_{k.strftime('%H%M')}Z",
                "cutoff": k - CUTOFF_LEAD, "no_events": True}
        a.no_props = a.no_lines = True
    else:
        slot = pick_slot(slots_from_events(events), now, None if a.slot == "next" else a.slot_kickoff)
    if slot is None:
        print("no matching slot in the events list (game moved, finished, or wrong --slot-kickoff)", file=sys.stderr)
        return 1
    markets = [m for m in (a.markets or ",".join(CORE_MARKETS)).split(",") if m]
    reserve = a.reserve if a.reserve is not None else RESERVE_BY_WEEK.get(a.week, 60)
    out_dir = Path(a.out)
    already = props_already_captured(out_dir, a.season, a.week) if out_dir.exists() else {}
    todo = [e for e in slot["events"] if e["id"] not in already]
    print(f"slot {slot['label']} week {a.week}: {len(slot['events'])} game(s), first kickoff {iso(slot['first_kickoff'])}, "
          f"cutoff target {iso(slot['cutoff'])}")
    for e in slot["events"]:
        tag = f"  (props already in {already[e['id']]})" if e["id"] in already else ""
        print(f"  {e['commence_time']}  {e.get('away_team')} @ {e.get('home_team')}{tag}")
    print(f"max cost: props {0 if a.no_props else len(todo) * len(markets)} + lines {0 if a.no_lines else 2}; "
          f"remaining {remaining:.0f}; reserve {reserve}")
    if a.dry_run:
        return 0

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    folder = out_dir / f"slot_{a.season}_w{a.week:02d}_{slot['label']}_{stamp}"
    folder.mkdir(parents=True, exist_ok=False)
    files: dict[str, str] = {}
    steps: dict[str, dict] = {}
    t0 = now
    try:
        steps["sleeper"] = step_sleeper(folder, a.season, a.week, files)
    except Exception as e:  # noqa: BLE001
        steps["sleeper"] = {"status": "FAILED", "error": repr(e)}
    if a.no_props:
        steps["props"] = {"status": "SKIPPED_NO_EVENTS" if slot.get("no_events") else "SKIPPED_BY_FLAG"}
    else:
        try:
            steps["props"] = step_props(folder, key, slot, markets, reserve, already, events_body, remaining, files)
        except Exception as e:  # noqa: BLE001
            steps["props"] = {"status": "FAILED", "error": repr(e)}
    if a.no_lines:
        steps["lines"] = {"status": "SKIPPED_NO_EVENTS" if slot.get("no_events") else "SKIPPED_BY_FLAG"}
    else:
        try:
            steps["lines"] = step_lines(folder, key, a.season, a.week, slot, stamp, files)
        except Exception as e:  # noqa: BLE001
            steps["lines"] = {"status": "FAILED", "error": repr(e)}
    for name, s in steps.items():
        if s.get("status") == "FAILED":
            s["fallback"] = previous_ok(out_dir, a.season, a.week, name, folder)
            s["fallback_rule"] = "use the named earlier slot folder of this week for this step; flagged, never silent"
    finished = datetime.now(timezone.utc)
    late = t0 >= slot["first_kickoff"]
    manifest = {
        "schema": "fie-lab-slot-capture-v1", "script_version": VERSION, "season": a.season, "week": a.week,
        "slot": {"label": slot["label"], "first_kickoff": iso(slot["first_kickoff"]), "cutoff_target": iso(slot["cutoff"]),
                 "games": [{"event_id": e["id"], "game": f"{e.get('away_team')} @ {e.get('home_team')}",
                            "commence_time": e.get("commence_time")} for e in slot["events"]]},
        "captured_at": iso(t0), "finished_at": iso(finished),
        "minutes_before_first_kickoff": round((slot["first_kickoff"] - t0).total_seconds() / 60, 1),
        "timing": "LATE_AFTER_KICKOFF" if late else
                  ("EARLY" if t0 < slot["cutoff"] - timedelta(minutes=30) else "ON_TIME"),
        "steps": steps,
        "aligned_pairs": aligned_pairs(slot, steps.get("props", {}), steps["sleeper"].get("status") == "OK", folder.name),
        "fie_availability": {"status": "NOT_COMPUTED_HERE",
                             "how": "py -3 -m fie_lab.weekly_run --week W --odds <this folder>/<odds file> --sunday <this folder>",
                             "why": "the F1 rules live in the frozen engine; this script never re-implements them"},
        "files": files,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    bad = [k for k, s in steps.items() if s.get("status") == "FAILED" or s.get("status") == "SKIPPED_NO_EVENTS"]
    line = (f"{iso(datetime.now(timezone.utc))} slot {slot['label']} w{a.week} -> {folder.name}: "
            + ", ".join(f"{k} {s.get('status')}" for k, s in steps.items()) + f"; timing {manifest['timing']}")
    with (out_dir / "slot_capture.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)
    return 3 if bad or late else 0


def parse(argv=None):
    ap = argparse.ArgumentParser(description="Decision snapshot for one kickoff slot (Sleeper + props + lines).")
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--season", type=int, default=2026)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--slot", choices=["next"], help="the next slot that has not kicked off")
    g.add_argument("--slot-kickoff", help="UTC ISO time of the slot's first kickoff (what the scheduled tasks pass)")
    ap.add_argument("--out", default="slots")
    ap.add_argument("--markets", help="comma list; default the 7 core markets (December: drop player_kicking_points)")
    ap.add_argument("--reserve", type=int, help="never go below this many remaining credits")
    ap.add_argument("--no-props", action="store_true")
    ap.add_argument("--no-lines", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse()))
