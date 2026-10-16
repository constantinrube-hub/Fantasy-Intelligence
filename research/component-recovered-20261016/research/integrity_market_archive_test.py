#!/usr/bin/env python3
"""Deterministic immutable Sleeper market-archive integrity checks."""
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta, timezone
import gzip, json
import pandas as pd

from build_current_snapshot import archive_sleeper_projection, market_capture_decision, regular_schedule_slice, resolve_analysis_week
from fie_m4 import load_sleeper_market

rows=[{"player_id":"1","player":{"position":"WR"},"stats":{"rec":5,"rec_yd":70}}]
ident=pd.DataFrame([{"sleeper_id":"1","canonical_player_id":"00-0030001"}])
now=datetime(2026,9,10,10,0,tzinfo=timezone.utc)
ctx=market_capture_decision("regular",now+timedelta(hours=8),now=now,window_hours=18)
assert ctx["pregame_eligible"] is True and ctx["capture_policy_version"]==2
assert market_capture_decision("preseason",now+timedelta(hours=8),now=now)["pregame_eligible"] is False
assert resolve_analysis_week(None,3,"preseason")==1
assert resolve_analysis_week(None,3,"regular")==3
assert resolve_analysis_week(7,3,"preseason")==7
assert market_capture_decision("regular",now+timedelta(hours=30),now=now)["reason"]=="before_capture_window"
sched=pd.DataFrame([
    {"season":2026,"week":3,"game_type":"PRE","home_team":"A","away_team":"B"},
    {"season":2026,"week":3,"game_type":"REG","home_team":"C","away_team":"D"},
])
reg=regular_schedule_slice(sched,2026,3)
assert len(reg)==1 and reg.iloc[0]["home_team"]=="C"

with TemporaryDirectory() as td:
    root=Path(td)
    first=archive_sleeper_projection(rows,2026,1,ident,root,True,capture_context=ctx)
    assert first["written"] is True
    assert first["pregame_eligible"] is True
    assert first["capture_policy_version"]==2
    assert len(first["sha256"])==64
    snap=Path(first["path"]); original=snap.read_bytes()
    manifest=json.loads((root/"manifest.json").read_text())
    assert manifest["snapshots"]["2026-W01"]["sha256"]==first["sha256"]
    assert manifest["snapshots"]["2026-W01"]["pregame_eligible"] is True
    assert manifest["snapshots"]["2026-W01"]["season_type"]=="regular"

    market,meta=load_sleeper_market(str(root),{"rec":1.0},ident)
    assert len(market)==1 and meta["timing_rejected_files"]==0

    # A later endpoint response cannot overwrite a first-write snapshot.
    second=archive_sleeper_projection([{"player_id":"1","stats":{"rec":99}}],2026,1,ident,root,False)
    assert second["written"] is False
    assert snap.read_bytes()==original
    assert second["sha256"]==first["sha256"]
    assert second["pregame_eligible"] is True

    # Tampering is fail-closed on the next registration attempt.
    with gzip.open(snap,"wt",encoding="utf-8") as h:
        h.write(json.dumps({"season":2026,"week":1,"pregame_eligible":True,"stats":{}})+"\n")
    try:
        archive_sleeper_projection(rows,2026,1,ident,root,True,capture_context=ctx)
    except RuntimeError as e:
        assert "hash changed" in str(e)
    else:
        raise AssertionError("tampered archive was not rejected")

with TemporaryDirectory() as td:
    root=Path(td)
    # Captures do not need a mutable canonical-ID enrichment step. The raw
    # Sleeper ID can be mapped later at evaluation time without touching bytes.
    raw=archive_sleeper_projection(rows,2026,2,pd.DataFrame(),root,True,capture_context=ctx)
    assert raw["written"] is True
    market,meta=load_sleeper_market(str(root),{"rec":1.0},ident)
    assert len(market)==1
    assert market.iloc[0]["canonical_player_id"]=="00-0030001"
    assert meta["posthoc_identity_mapped_rows"]==1

with TemporaryDirectory() as td:
    root=Path(td); out=root/"2026"/"week_03.jsonl.gz"; out.parent.mkdir(parents=True)
    with gzip.open(out,"wt",encoding="utf-8") as h:
        h.write(json.dumps({"season":2026,"week":3,"pregame_eligible":True,"sleeper_id":"1","stats":{"rec":4}})+"\n")
    # Legacy/unverified "eligible" files are now rejected by M4 itself.
    market,meta=load_sleeper_market(str(root),{"rec":1.0},ident)
    assert market.empty and meta["timing_rejected_files"]==1

print("OK immutable Sleeper market archive + unified timing policy")
