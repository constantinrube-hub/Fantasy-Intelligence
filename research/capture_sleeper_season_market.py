#!/usr/bin/env python3
"""Freeze a Sleeper season projection/ADP market snapshot for M9 reports.

Sleeper's projection endpoint is intentionally treated as an optional market feed,
not a source of truth for FIE football outcomes.  The snapshot stores all ADP fields
published by Sleeper so each league can later select the correct 1QB/SF/PPR/dynasty
market without recapturing the market after results are known.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

UA = "Fantasy-Intelligence-V9.4-M9/1.0"
ADP_KEYS = [
    "adp_dynasty_2qb", "adp_dynasty_ppr", "adp_dynasty_half_ppr", "adp_dynasty_std",
    "adp_2qb", "adp_ppr", "adp_half_ppr", "adp_std", "adp_idp", "adp_idp_1qb",
]


def now(): return datetime.now(timezone.utc).isoformat()


def norm_sleeper_id(value: object) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none"}:
        return ""
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    return s


def sleeper_full_name(player: dict, row: dict) -> str | None:
    explicit = player.get("full_name") or row.get("full_name")
    if explicit:
        return str(explicit).strip() or None
    parts = [player.get("first_name") or row.get("first_name"),
             player.get("last_name") or row.get("last_name")]
    name = " ".join(str(x).strip() for x in parts if x not in (None, ""))
    return name or None


def get_json(url):
    r = requests.get(url, timeout=45, headers={"User-Agent": UA, "Accept": "application/json"})
    r.raise_for_status(); return r.json()


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--derived-dir", default="data/research/derived")
    p.add_argument("--output-root", default="data/research/market/sleeper")
    p.add_argument("--as-of", default=None, help="Snapshot date YYYY-MM-DD; defaults to UTC capture date")
    p.add_argument("--force", action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv); captured = now(); day = a.as_of or captured[:10]
    out = Path(a.output_root) / str(a.season) / f"season_market_{day}.jsonl.gz"
    if out.exists() and not a.force:
        print(f"Immutable market snapshot already exists: {out}"); return
    ident_path = Path(a.derived_dir) / "player_identity.csv.gz"
    ident = pd.read_csv(ident_path, low_memory=False) if ident_path.exists() else pd.DataFrame()
    by_sid = {}
    if not ident.empty and "sleeper_id" in ident:
        for r in ident.dropna(subset=["sleeper_id"]).itertuples(index=False):
            sid = norm_sleeper_id(getattr(r, "sleeper_id"))
            if not sid:
                continue
            by_sid[sid] = {
                "canonical_player_id": str(getattr(r, "canonical_player_id", "") or "") or None,
                "full_name": getattr(r, "full_name", None), "position_model": getattr(r, "position", None),
            }
    payload = get_json(f"https://api.sleeper.com/projections/nfl/{a.season}?season_type=regular") or []
    if isinstance(payload, dict):
        rows = payload.get('projections') or payload.get('players') or payload.get('data') or []
    else:
        rows = payload
    if not isinstance(rows, list):
        raise RuntimeError('Sleeper season projection payload is not a list-like projection feed')
    out.parent.mkdir(parents=True, exist_ok=True); kept = 0
    with gzip.open(out, "wt", encoding="utf-8") as h:
        for r in rows:
            sid = norm_sleeper_id(r.get("player_id") or (r.get("player") or {}).get("player_id"))
            if not sid: continue
            stats = r.get("stats") or r; player = r.get("player") or {}; ident_row = by_sid.get(sid, {})
            adp = {k: (stats.get(k) if stats.get(k) is not None else r.get(k)) for k in ADP_KEYS if (stats.get(k) is not None or r.get(k) is not None)}
            rec = {
                "season": int(a.season), "captured_at": captured, "market_as_of": day,
                "source": "Sleeper season projection endpoint", "sleeper_id": sid,
                "canonical_player_id": ident_row.get("canonical_player_id"),
                "full_name": ident_row.get("full_name") or sleeper_full_name(player, r),
                "position_model": ident_row.get("position_model") or player.get("position") or r.get("position"),
                "team": player.get("team") or r.get("team"), "adp": adp, "stats": stats,
            }
            h.write(json.dumps(rec, separators=(",", ":")) + "\n"); kept += 1
    meta = out.with_suffix(out.suffix + ".meta.json")
    meta.write_text(json.dumps({"season": a.season, "captured_at": captured, "market_as_of": day,
                                "rows": kept, "source": "Sleeper season projection endpoint",
                                "immutable_first_write": not a.force, "adp_keys": ADP_KEYS}, indent=2))
    print(f"Wrote {out} rows={kept}")


if __name__ == "__main__": main()
