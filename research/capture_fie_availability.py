#!/usr/bin/env python3
"""Capture immutable point-in-time Sleeper offensive availability evidence.

This archive exists for future injury/opportunity-redistribution research.  It stores
only fields observable at capture time and never backfills or reconstructs an old day.
Rows are keyed by Sleeper player_id; canonical identity is joined later through FIE's
existing identity table so the evidence archive does not depend on one league cache.
"""
from __future__ import annotations

import argparse
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE = "Sleeper /v1/players/nfl"
URL = "https://api.sleeper.app/v1/players/nfl"
POSITIONS = {"QB", "RB", "WR", "TE"}
FIELDS = (
    "status", "injury_status", "injury_body_part", "injury_notes",
    "practice_participation", "practice_description", "depth_chart_order",
    "depth_chart_position", "years_exp", "age",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_players() -> dict:
    req = Request(URL, headers={"User-Agent":"Fantasy-Intelligence-Availability/1.0", "Accept":"application/json"})
    with urlopen(req, timeout=45) as r:
        if r.status != 200:
            raise RuntimeError(f"Sleeper player endpoint returned HTTP {r.status}")
        obj = json.loads(r.read().decode("utf-8"))
    if not isinstance(obj, dict) or len(obj) < 500:
        raise RuntimeError("Sleeper player payload unexpectedly small or invalid")
    return obj


def fixture_players() -> dict:
    return {
        "1":{"player_id":"1","full_name":"Fixture RB","team":"AAA","position":"RB","status":"Active","injury_status":None,"depth_chart_order":1},
        "2":{"player_id":"2","full_name":"Fixture WR","team":"BBB","position":"WR","status":"Inactive","injury_status":"Out","injury_body_part":"Hamstring","depth_chart_order":2},
        "3":{"player_id":"3","full_name":"Fixture CB","team":"CCC","position":"CB","status":"Active"},
    }


def compact(raw: dict, captured_at: str, day: str) -> list[dict]:
    rows=[]
    for key, p in raw.items():
        if not isinstance(p, dict):
            continue
        sid=str(p.get("player_id") or key or "").strip()
        team=str(p.get("team") or "").strip().upper()
        pos=str(p.get("position") or "").strip().upper()
        if not sid or not team or pos not in POSITIONS:
            continue
        name=str(p.get("full_name") or " ".join(str(p.get(x) or "").strip() for x in ("first_name","last_name")).strip()).strip()
        row={
            "captured_at":captured_at,
            "availability_as_of":day,
            "source":SOURCE,
            "sleeper_id":sid,
            "full_name":name or None,
            "team":team,
            "position_model":pos,
        }
        for f in FIELDS:
            if p.get(f) is not None:
                row[f]=p.get(f)
        rows.append(row)
    rows.sort(key=lambda x:(x["position_model"],x["team"],x["sleeper_id"]))
    return rows


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--output-root",default="data/research/availability/sleeper")
    p.add_argument("--as-of",default=None,help="UTC evidence date YYYY-MM-DD; defaults to capture date")
    p.add_argument("--fixture",action="store_true")
    a=p.parse_args(argv)
    captured=now_iso(); day=a.as_of or captured[:10]
    if len(day)!=10 or day[4]!="-" or day[7]!="-":
        raise SystemExit("--as-of must be YYYY-MM-DD")
    year=day[:4]; out=Path(a.output_root)/year/f"availability_{day}.jsonl.gz"
    meta=out.with_suffix(out.suffix+".meta.json")
    if out.exists():
        print(f"Immutable availability snapshot already exists: {out}")
        return
    rows=compact(fixture_players() if a.fixture else fetch_players(),captured,day)
    if not rows:
        raise RuntimeError("Availability snapshot produced zero offensive players")
    out.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(out,"wt",encoding="utf-8") as h:
        for row in rows:
            h.write(json.dumps(row,separators=(",",":"),allow_nan=False)+"\n")
    injured=sum(1 for r in rows if r.get("injury_status"))
    meta.write_text(json.dumps({
        "captured_at":captured,"availability_as_of":day,"source":SOURCE,"rows":len(rows),
        "positions":sorted(POSITIONS),"rows_with_injury_status":injured,"immutable_first_write":True,
        "semantics":"prospective point-in-time evidence; no historical reconstruction",
    },indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {out} rows={len(rows)} injury_status={injured}")


if __name__=="__main__":
    main()
