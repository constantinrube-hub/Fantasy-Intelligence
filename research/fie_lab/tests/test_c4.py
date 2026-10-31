"""test_c4.py - offline tests for slot_capture.py, slot_schedule.py and fie_paired_sleeper_eval.py v2.

Usage: python -I test_c4.py   (from the folder holding the scripts; v1 of the eval in ./v1 for T13)
The network is replaced by a fake HTTP layer (Sleeper + The Odds API) with a credit counter.
"""
from __future__ import annotations

import contextlib
import csv
import gzip
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Works in the build folder (scripts next to this file, v1/ and v2/ subfolders) and in the repo
# (research/fie_lab/tests/: scripts one level up, registered v1 next to this file).
SCRIPTS = HERE if (HERE / "slot_capture.py").exists() else HERE.parent
V1 = next(p for p in (HERE / "v1/fie_paired_sleeper_eval.py", HERE / "fie_paired_sleeper_eval_v1.py") if p.exists())
V2 = next(p for p in (HERE / "v2/fie_paired_sleeper_eval.py", SCRIPTS / "fie_paired_sleeper_eval.py") if p.exists())
sys.path.insert(0, str(SCRIPTS))
import slot_capture as sc  # noqa: E402
import slot_schedule as ss  # noqa: E402

KEY = "TESTKEY-must-never-be-written-1234567890"
# Week 9 2026 (Berlin = UTC+1): TNF Fri 01:15, Sun 14:30 intl, 18:00 early (x3), 21:05 + 21:25 late, SNF 01:20 Mon, MNF 01:15 Tue
EVENTS = [
    {"id": "e_tnf", "commence_time": "2026-11-06T01:15:00Z", "home_team": "Kansas City Chiefs", "away_team": "Denver Broncos"},
    {"id": "e_intl", "commence_time": "2026-11-08T14:30:00Z", "home_team": "Miami Dolphins", "away_team": "Buffalo Bills"},
    {"id": "e_e1", "commence_time": "2026-11-08T18:00:00Z", "home_team": "Detroit Lions", "away_team": "Chicago Bears"},
    {"id": "e_e2", "commence_time": "2026-11-08T18:00:00Z", "home_team": "Atlanta Falcons", "away_team": "New Orleans Saints"},
    {"id": "e_e3", "commence_time": "2026-11-08T18:00:00Z", "home_team": "Cincinnati Bengals", "away_team": "Tennessee Titans"},
    {"id": "e_l1", "commence_time": "2026-11-08T21:05:00Z", "home_team": "Seattle Seahawks", "away_team": "Arizona Cardinals"},
    {"id": "e_l2", "commence_time": "2026-11-08T21:25:00Z", "home_team": "Los Angeles Rams", "away_team": "San Francisco 49ers"},
    {"id": "e_snf", "commence_time": "2026-11-09T01:20:00Z", "home_team": "Philadelphia Eagles", "away_team": "Dallas Cowboys"},
    {"id": "e_mnf", "commence_time": "2026-11-10T01:15:00Z", "home_team": "Pittsburgh Steelers", "away_team": "Baltimore Ravens"},
    # next week's Thursday game: must never enter week 9 lines or slots
    {"id": "e_w10", "commence_time": "2026-11-13T01:15:00Z", "home_team": "New York Jets", "away_team": "New England Patriots"},
]


class Fake:
    def __init__(self, credits=500, fail_sleeper=False, fail_props_for=()):
        self.credits, self.fail_sleeper, self.fail_props_for, self.calls = credits, fail_sleeper, set(fail_props_for), []

    def __call__(self, url, timeout=120):
        self.calls.append(url)
        u = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(u.query)
        if "sleeper" in u.netloc:
            if self.fail_sleeper:
                raise OSError("network down")
            if u.path.startswith("/projections"):
                pos = (q.get("position[]") or ["ALL"])[0]
                rows = [{"player_id": f"{pos}{i}", "stats": {"pts_ppr": 10 + i}} for i in range(3)]
                return 200, json.dumps(rows).encode(), {}
            if u.path == "/v1/players/nfl":
                players = {"4046": {"full_name": "Patrick Mahomes", "team": "KC", "position": "QB", "fantasy_positions": ["QB"],
                                    "injury_status": None, "gsis_id": "00-0033873"},
                           "9999": {"full_name": "Some LB", "team": "DET", "position": "LB", "fantasy_positions": ["LB"],
                                    "injury_status": "Questionable"},
                           "1111": {"full_name": "OL Guy", "team": "DET", "position": "OL", "fantasy_positions": ["OL"]},
                           "KC": {"team": "KC", "position": "DEF", "fantasy_positions": ["DEF"]}}
                return 200, json.dumps(players).encode(), {}
        if "the-odds-api" in u.netloc:
            assert q.get("apiKey") == [KEY]
            hdr = lambda cost: {"x-requests-last": str(cost), "x-requests-used": str(500 - self.credits),
                                "x-requests-remaining": str(self.credits)}
            if u.path.endswith("/events"):
                return 200, json.dumps(EVENTS).encode(), hdr(0)
            if u.path.endswith("/odds") and "/events/" in u.path:
                eid = u.path.split("/events/")[1].split("/")[0]
                if eid in self.fail_props_for:
                    return 500, b'{"message":"boom"}', hdr(0)
                markets = q["markets"][0].split(",")
                returned = markets[:-1]  # one market not posted (costs nothing)
                self.credits -= len(returned)
                body = {"id": eid, "bookmakers": [{"key": "dk", "markets": [{"key": m, "outcomes": []} for m in returned]}]}
                return 200, json.dumps(body).encode(), hdr(len(returned))
            if u.path.endswith("/odds"):
                self.credits -= 2
                body = [dict(e, bookmakers=[]) for e in EVENTS if e["commence_time"] > "2026-11-05"]
                return 200, json.dumps(body).encode(), hdr(2)
        raise AssertionError(url)


@contextlib.contextmanager
def fake(f):
    old = sc.http_get
    sc.http_get = f
    os.environ["ODDS_API_KEY"] = KEY
    try:
        yield f
    finally:
        sc.http_get = old


def run(out, now, argv, f):
    with fake(f), contextlib.redirect_stdout(io.StringIO()) as buf:
        code = sc.run(sc.parse(["--week", "9", "--out", str(out)] + argv), now=sc.utc(now))
    folders = sorted(Path(out).glob("slot_2026_w09_*"), key=lambda p: p.stat().st_mtime)
    return code, (json.loads((folders[-1] / "manifest.json").read_text()) if folders else None), folders, buf.getvalue()


def t1_slots():
    sl = sc.slots_from_events(EVENTS)
    labels = [s["label"] for s in sl]
    assert labels == ["FRI_0115Z", "SUN_1430Z", "SUN_1800Z", "SUN_2105Z", "MON_0120Z", "TUE_0115Z", "FRI_0115Z"], labels
    late = sl[3]
    assert [e["id"] for e in late["events"]] == ["e_l1", "e_l2"]           # 21:05 and 21:25 share the late slot
    assert sc.iso(late["cutoff"]) == "2026-11-08T19:50:00Z"                 # T-75 of 21:05 = 20:50 Berlin
    assert sc.iso(sc.week_end(sc.utc("2026-11-06T01:15:00Z"))) == "2026-11-11T12:00:00Z"
    assert sc.iso(sc.week_end(sc.utc("2026-11-10T01:15:00Z"))) == "2026-11-11T12:00:00Z"
    return "slots: 7 from 10 games; late 21:05+21:25 merged; T-75 and week end correct"


def t2_capture_and_once_per_game(tmp):
    out = tmp / "slots"
    f = Fake()
    code, m, folders, _ = run(out, "2026-11-08T16:45:00Z", ["--slot-kickoff", "2026-11-08T18:00:00Z"], f)
    assert code == 0 and m["timing"] == "ON_TIME", (code, m["timing"])
    assert m["slot"]["label"] == "SUN_1800Z" and len(m["slot"]["games"]) == 3
    assert m["steps"]["sleeper"]["status"] == "OK" and m["steps"]["props"]["status"] == "OK" and m["steps"]["lines"]["status"] == "OK"
    assert all(p["aligned"] for p in m["aligned_pairs"])
    names = set(m["files"])
    for pos in sc.POSITIONS:   # sunday_capture.py file names (weekly_run --sunday compatibility)
        assert f"sleeper_projections_{pos}.json.gz" in names
    assert {"sleeper_players.json.gz", "sleeper_players_full.json.gz", "sleeper_projections_ALL.json.gz"} <= names
    compact = json.loads(gzip.open(folders[-1] / "sleeper_players.json.gz").read())
    assert set(compact) == {"4046", "9999", "KC"}   # IDP kept, OL dropped, team defence kept
    credits_after_first = f.credits
    assert credits_after_first == 500 - 3 * 6 - 2   # 3 games x 6 returned markets + 2 for lines
    # same slot again (e.g. a manual re-run): props must not be bought twice
    code, m2, folders, _ = run(out, "2026-11-08T17:00:00Z", ["--slot-kickoff", "2026-11-08T18:00:00Z", "--no-lines"], f)
    assert m2["steps"]["props"]["status"] == "SKIPPED_ALL_CAPTURED" and f.credits == credits_after_first
    assert all(not p["aligned"] and p["props_from"] == folders[0].name for p in m2["aligned_pairs"])
    return f"first run OK (20 credits, 3/3 aligned); re-run bought 0 props and marked pairs unaligned"


def t3_lines_filtered(tmp):
    out = tmp / "slots"
    code, m, folders, _ = run(out, "2026-11-08T20:00:00Z", ["--slot-kickoff", "2026-11-08T21:05:00Z"], Fake())
    lines = json.loads((folders[-1] / m["steps"]["lines"]["file"]).read_text())
    ids = {e["id"] for e in lines["response"]}
    assert "e_w10" not in ids and "e_mnf" in ids, ids
    assert lines["fie_lab_filter"]["games_in_source"] == 10 and lines["fie_lab_filter"]["games_kept"] == 9
    assert lines["schema"] == "fie-lab-odds-capture-v1"
    return "lines: next week's game dropped (9 of 10 kept), filter block + source hash recorded"


def t4_reserve(tmp):
    out = tmp / "slots"
    code, m, _, _ = run(out, "2026-11-08T16:45:00Z", ["--slot-kickoff", "2026-11-08T18:00:00Z", "--reserve", "490"],
                        Fake(credits=500))
    calls = m["steps"]["props"]["calls"]
    assert [c.get("skipped") for c in calls] == [None, "RESERVE", "RESERVE"], calls
    assert m["steps"]["props"]["status"] == "FAILED" and code == 3
    return "reserve: stops before going below it, flagged FAILED, exit 3"


def t5_failure_fallback_late(tmp):
    out = tmp / "slots"
    run(out, "2026-11-08T13:15:00Z", ["--slot-kickoff", "2026-11-08T14:30:00Z"], Fake())
    code, m, _, _ = run(out, "2026-11-08T18:05:00Z", ["--slot-kickoff", "2026-11-08T18:00:00Z"],
                        Fake(fail_sleeper=True, fail_props_for={"e_e2"}))
    assert code == 3 and m["timing"] == "LATE_AFTER_KICKOFF"
    assert m["steps"]["sleeper"]["status"] == "FAILED" and m["steps"]["sleeper"]["fallback"].startswith("slot_2026_w09_SUN_1430Z")
    assert m["steps"]["props"]["status"] == "FAILED" and m["steps"]["lines"]["status"] == "OK"
    assert not any(p["aligned"] for p in m["aligned_pairs"])
    log = (out / "slot_capture.log").read_text()
    assert "sleeper FAILED" in log and "LATE_AFTER_KICKOFF" in log
    return "Sleeper down + one props 500: other steps still run, fallback = earlier slot folder, LATE flagged, logged"


def t6_no_key(tmp):
    out = tmp / "slots"
    os.environ.pop("ODDS_API_KEY", None)
    old = sc.http_get
    sc.http_get = Fake()
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = sc.run(sc.parse(["--week", "9", "--out", str(out), "--slot-kickoff", "2026-11-08T18:00:00Z"]),
                          now=sc.utc("2026-11-08T16:45:00Z"))
            code_next = sc.run(sc.parse(["--week", "9", "--out", str(out), "--slot", "next"]), now=sc.utc("2026-11-08T16:45:00Z"))
    finally:
        sc.http_get = old
    m = json.loads(sorted(out.glob("slot_2026_*"))[-1].joinpath("manifest.json").read_text())
    assert code == 3 and m["steps"]["sleeper"]["status"] == "OK" and m["steps"]["props"]["status"] == "SKIPPED_NO_EVENTS"
    assert code_next == 2
    return "no key: Sleeper-only run with --slot-kickoff (flagged, exit 3); --slot next refuses (exit 2)"


def t7_key_never_on_disk(tmp):
    hits = [str(p) for p in tmp.rglob("*") if p.is_file() and KEY.encode() in
            (gzip.open(p).read() if p.suffix == ".gz" else p.read_bytes())]
    assert not hits, hits
    return f"API key absent from all {sum(1 for p in tmp.rglob('*') if p.is_file())} written files"


def t8_dry_run(tmp):
    out = tmp / "dry"
    code, m, folders, text = run(out, "2026-11-08T16:45:00Z", ["--slot", "next", "--dry-run"], Fake())
    assert code == 0 and not folders and "max cost: props 21 + lines 2" in text, text
    return "dry run: buys and writes nothing, prints max cost"


def t9_schedule(tmp):
    ev = tmp / "events.json"
    ev.write_text(json.dumps(EVENTS))
    out = tmp / "sched"
    with contextlib.redirect_stdout(io.StringIO()):
        code = ss.main(["--week", "9", "--lab", "C:\\Users\\User\\FIE\\FIE-Lab", "--out", str(out), "--events", str(ev)])
    assert code == 0
    rows = json.loads((out / "slots_w09.json").read_text())
    # generated "now" is real time; slots are those of the earliest upcoming game's week
    reg = (out / "register_slots_w09.ps1").read_text(encoding="utf-8-sig")
    unreg = (out / "unregister_slots_w09.ps1").read_text(encoding="utf-8-sig")
    assert "-WakeToRun" in reg and "-StartWhenAvailable" in reg and "Register-ScheduledTask" in reg
    assert reg.count("Register-ScheduledTask") == len(rows) == unreg.count("Unregister-ScheduledTask")
    # fixed-clock check of the slot set and start times
    sl = ss.week_slots(EVENTS, sc.utc("2026-11-03T20:00:00Z"))
    r2 = ss.render(sl, 9, 2026, "C:\\Users\\User\\FIE\\FIE-Lab", "py -3", 80, "C:\\Users\\User\\FIE\\FIE-Lab\\slots")[2]
    assert [r["start_utc"] for r in r2] == ["2026-11-05T23:55:00Z", "2026-11-08T13:10:00Z", "2026-11-08T16:40:00Z",
                                           "2026-11-08T19:45:00Z", "2026-11-09T00:00:00Z", "2026-11-09T23:55:00Z"], r2
    assert all(r["task"].startswith("FIE Slot W09 ") for r in r2) and sum(r["games"] for r in r2) == 9
    text = ss.render(sl, 9, 2026, "C:\\Users\\User\\FIE\\FIE-Lab", "py -3", 80, "C:\\Users\\User\\FIE\\FIE-Lab\\slots")[0]
    assert "-Execute 'py' -Argument '-3 \"C:\\Users\\User\\FIE\\FIE-Lab\\slot_capture.py\" --week 9" in text
    assert KEY not in reg
    return "schedule: 6 tasks for week 9 (next week's game excluded), T-80 starts in UTC, wake + catch-up settings"


# ---------------------------------------------------------------- paired eval v2 vs registered v1
def fixture_repo(root: Path, weeks):
    rng = random.Random(3)
    base = root / "data/research"
    xw = ["sleeper_id,gsis_id"]
    for w in weeks:
        sl, fc, oc = [], [], []
        for i in range(60):
            pos = ["QB", "RB", "WR", "TE"][i % 4]
            gid, sid = f"00-00{i:05d}", f"{1000 + i}"
            if w == weeks[0]:
                xw.append(f"{sid},{gid}")
            truth = rng.uniform(2, 25)
            s_proj, m_proj = truth + rng.gauss(0, 4), truth + rng.gauss(0, 5)
            sl.append({"sleeper_id": sid, "captured_at": f"2026-10-{w + 1:02d}T06:00:00Z", "stats": {"rec": s_proj}})
            fid = f"2026-{w:02d}-{gid}"
            for model, val in (("M10_HGB", m_proj), ("M9", m_proj + 0.3)):
                fc.append({"forecast_id": fid, "model": model, "position_model": pos, "captured_at": "x",
                           "predicted_fantasy_points_default": val})
            oc.append({"forecast_id": fid, "canonical_player_id": gid,
                       "status": "OBSERVED_PROVIDER_ROW" if i % 7 else "NO_PROVIDER_ROW",
                       "raw_outcomes": {"fantasy_points_ppr": max(0.0, truth + rng.gauss(0, 3))}})
        for rel, rows in ((f"market/sleeper/2026/week_{w:02d}.jsonl.gz", sl),
                          (f"prospective/m10/forecasts/2026/week_{w:02d}/forecast.jsonl.gz", fc),
                          (f"prospective/m10/outcomes/2026/week_{w:02d}/revision_1/outcomes.jsonl.gz", oc)):
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(p, "wt") as fh:
                fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
    (root / "xw.csv").write_text("\n".join(xw) + "\n")


def evalrun(script: Path, args):
    return subprocess.run([sys.executable, "-I", str(script)] + args, capture_output=True, text=True)


def t10_eval_v1_identity(tmp):
    repo = tmp / "repo"
    fixture_repo(repo, list(range(4, 11)))
    v1, v2 = V1, V2
    for weeks in ("4-7", "4-10"):
        out = tmp / "rows.csv"  # same path for both: the last stdout line names the CSV file
        a = evalrun(v1, ["--repo", str(repo), "--weeks", weeks, "--crosswalk", str(repo / "xw.csv"), "--csv", str(out)])
        a_csv = out.read_bytes()
        b = evalrun(v2, ["--repo", str(repo), "--weeks", weeks, "--crosswalk", str(repo / "xw.csv"), "--csv", str(out)])
        assert a.returncode == b.returncode == 0, (a.stderr, b.stderr)
        assert a.stdout == b.stdout, "stdout differs"
        assert a_csv == out.read_bytes(), "csv differs"
    return "v2 without new options: stdout and CSV byte-identical to registered v1 (weeks 4-7 and 4-10)"


def t11_eval_blend(tmp):
    repo = tmp / "repo"
    v2 = V2
    b = evalrun(v2, ["--repo", str(repo), "--weeks", "4-10", "--crosswalk", str(repo / "xw.csv"), "--blend", "--csv", str(tmp / "c.csv")])
    assert b.returncode == 0, b.stderr
    assert "VERDICT (registered rule)" in b.stdout and "RETROSPECTIVE" in b.stdout and "B75" in b.stdout
    rows = list(csv.DictReader(open(tmp / "c.csv")))
    r = rows[0]
    assert abs(float(r["B75"]) - (0.75 * float(r["SLEEPER"]) + 0.25 * float(r["M10_HGB"]))) < 1e-9
    i = evalrun(v2, ["--repo", str(repo), "--weeks", "4-9", "--crosswalk", str(repo / "xw.csv"), "--blend"])
    assert "INTERIM: description only" in i.stdout and "VERDICT" not in i.stdout
    # Spearman helper: ties averaged, perfect monotone = 1
    import importlib.util
    spec = importlib.util.spec_from_file_location("pe2", v2)
    pe2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pe2)
    assert pe2.ranks([3, 1, 3, 2]) == [3.5, 1.0, 3.5, 2.0]
    assert abs(pe2.spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1) < 1e-12
    return "--blend: B75 = 0.75 S + 0.25 M10 exactly; VERDICT only with Weeks 8-10 complete, INTERIM otherwise"


def t12_crosswalk_archive(tmp):
    repo = tmp / "repo"
    v2 = V2
    arc = tmp / "xw_archive"
    b = evalrun(v2, ["--repo", str(repo), "--weeks", "4", "--crosswalk", str(repo / "xw.csv"), "--crosswalk-archive", str(arc)])
    assert "crosswalk file:" in b.stdout and "sha256" in b.stdout
    # the download path archives a dated copy once and reuses it for identical content
    import importlib.util
    spec = importlib.util.spec_from_file_location("pe2", v2)
    pe2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pe2)
    text = (repo / "xw.csv").read_text()
    p1 = pe2.archive_crosswalk(text, str(arc))
    p2 = pe2.archive_crosswalk(text, str(arc))
    assert p1 == p2 and len(list(arc.glob("db_playerids_*.csv"))) == 1 and Path(p1 + ".sha256").exists()
    return "--crosswalk-archive: dated copy written once, identical content reused, hash printed"


def main():
    results = {}
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for name, fn in [("T1", t1_slots), ("T2", t2_capture_and_once_per_game), ("T3", t3_lines_filtered),
                         ("T4", t4_reserve), ("T5", t5_failure_fallback_late), ("T6", t6_no_key), ("T8", t8_dry_run),
                         ("T9", t9_schedule), ("T7", t7_key_never_on_disk), ("T10", t10_eval_v1_identity),
                         ("T11", t11_eval_blend), ("T12", t12_crosswalk_archive)]:
            sub = tmp / name
            sub.mkdir()
            if name == "T7":
                sub = tmp
            if name in ("T11", "T12"):
                sub = tmp / "T10"
            results[name] = (fn(sub) if fn.__code__.co_argcount else fn())
            print(f"PASS {name}: {results[name]}")
    print(f"\nALL {len(results)} PASS")


if __name__ == "__main__":
    main()
