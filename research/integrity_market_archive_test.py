#!/usr/bin/env python3
"""Deterministic immutable Sleeper market-archive integrity checks."""
from pathlib import Path
from tempfile import TemporaryDirectory
import gzip, json
import pandas as pd

from build_current_snapshot import archive_sleeper_projection
from fie_m4 import load_sleeper_market

rows=[{"player_id":"1","player":{"position":"WR"},"stats":{"rec":5,"rec_yd":70}}]
ident=pd.DataFrame([{"sleeper_id":"1","canonical_player_id":"00-0030001"}])

with TemporaryDirectory() as td:
    root=Path(td)
    first=archive_sleeper_projection(rows,2026,1,ident,root,True)
    assert first["written"] is True
    assert first["pregame_eligible"] is True
    assert len(first["sha256"])==64
    snap=Path(first["path"]); original=snap.read_bytes()
    manifest=json.loads((root/"manifest.json").read_text())
    assert manifest["snapshots"]["2026-W01"]["sha256"]==first["sha256"]
    assert manifest["snapshots"]["2026-W01"]["pregame_eligible"] is True

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
        archive_sleeper_projection(rows,2026,1,ident,root,True)
    except RuntimeError as e:
        assert "hash changed" in str(e)
    else:
        raise AssertionError("tampered archive was not rejected")

with TemporaryDirectory() as td:
    root=Path(td)
    # Captures do not need a mutable canonical-ID enrichment step.  The raw
    # Sleeper ID can be mapped later at evaluation time without touching bytes.
    raw=archive_sleeper_projection(rows,2026,2,pd.DataFrame(),root,True)
    assert raw["written"] is True
    market,meta=load_sleeper_market(str(root),{"rec":1.0},ident)
    assert len(market)==1
    assert market.iloc[0]["canonical_player_id"]=="00-0030001"
    assert meta["posthoc_identity_mapped_rows"]==1

print("OK immutable Sleeper market archive")
