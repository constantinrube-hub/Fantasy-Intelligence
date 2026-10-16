#!/usr/bin/env python3
"""Immutable observed Sleeper availability for offense, IDP and kickers.

Provider status is evidence, not a probability of playing or an injury model.
Missing fields remain unknown. Existing daily archives are never rewritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SOURCE = "Sleeper /v1/players/nfl"
URL = "https://api.sleeper.app/v1/players/nfl"
CONTRACT = "fie-availability-offense-idp-k-v1"
OFFENSIVE_POSITIONS = {"QB", "RB", "WR", "TE"}
IDP_POSITIONS = {"DL", "DE", "DT", "NT", "EDGE", "LEO", "LB", "ILB", "OLB", "DB", "CB", "S", "FS", "SS"}
KICKER_POSITIONS = {"K", "K/P"}
POSITIONS = OFFENSIVE_POSITIONS | IDP_POSITIONS | KICKER_POSITIONS
TEAM_POSITIONS = {"DEF", "DST", "D/ST"}
FIELDS = (
    "status", "injury_status", "injury_body_part", "injury_notes",
    "practice_participation", "practice_description", "depth_chart_order",
    "depth_chart_position", "years_exp", "age", "injury_start_date", "news_updated", "active",
)
BERLIN = ZoneInfo("Europe/Berlin")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Capture timestamp must include its timezone")
    return parsed.astimezone(timezone.utc)


def automatic_capture_allowed(as_of: str) -> bool:
    local = parse_time(as_of).astimezone(BERLIN)
    return local.month >= 9 or (local.month == 1 and local.day <= 10)


def football_season(as_of: str) -> int:
    local = parse_time(as_of).astimezone(BERLIN)
    return local.year if local.month >= 9 else local.year - 1


def fetch_players() -> dict:
    req = Request(URL, headers={"User-Agent": "Fantasy-Intelligence-Availability/1.1", "Accept": "application/json"})
    with urlopen(req, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"Sleeper player endpoint returned HTTP {response.status}")
        obj = json.loads(response.read().decode("utf-8"))
    if not isinstance(obj, dict) or len(obj) < 500:
        raise RuntimeError("Sleeper player payload unexpectedly small or invalid")
    return obj


def fixture_players() -> dict:
    return {
        "1": {"player_id": "1", "full_name": "Fixture RB", "team": "AAA", "position": "RB", "status": "Active", "injury_status": None, "depth_chart_order": 1},
        "2": {"player_id": "2", "full_name": "Fixture WR", "team": "BBB", "position": "WR", "status": "Inactive", "injury_status": "Out", "injury_body_part": "Hamstring", "depth_chart_order": 2},
        "3": {"player_id": "3", "full_name": "Fixture CB", "team": "CCC", "position": "CB", "fantasy_positions": ["DB"], "status": "Active"},
        "4": {"player_id": "4", "full_name": "Fixture K", "team": "CCC", "position": "K", "status": "Active", "practice_participation": "Limited"},
        "5": {"player_id": "5", "position": "LB", "team": None, "status": "Inactive", "active": False},
        "AAA": {"player_id": "AAA", "position": "DEF", "team": "AAA"},
    }


def group_for(row: dict) -> str:
    pos = row.get("position_model")
    fantasy = set(row.get("fantasy_positions") or [])
    if pos in OFFENSIVE_POSITIONS:
        return "OFFENSE"
    if pos in KICKER_POSITIONS or fantasy & KICKER_POSITIONS:
        return "KICKER"
    return "IDP"


def compact(raw: dict, captured_at: str, day: str) -> list[dict]:
    if not isinstance(raw, dict):
        raise ValueError("Availability source must be a player dictionary")
    rows, seen = [], set()
    for key, player in raw.items():
        if not isinstance(player, dict):
            raise ValueError(f"Malformed player record: {key}")
        sid = str(player.get("player_id") or key or "").strip()
        pos = str(player.get("position") or "").strip().upper()
        fantasy_raw = player.get("fantasy_positions")
        fantasy = {str(p).strip().upper() for p in fantasy_raw} if isinstance(fantasy_raw, list) else set()
        if pos in TEAM_POSITIONS or fantasy & TEAM_POSITIONS:
            continue
        if not sid or not (pos in POSITIONS or fantasy & (IDP_POSITIONS | KICKER_POSITIONS)):
            continue
        team = str(player.get("team") or "").strip().upper()
        # Keep the established offensive universe. IDP/K also includes free
        # agents/inactive catalog entries; an absent team is explicitly unknown.
        if pos in OFFENSIVE_POSITIONS and not team:
            continue
        if sid in seen:
            raise ValueError(f"Duplicate Sleeper player identity: {sid}")
        seen.add(sid)
        name = str(player.get("full_name") or " ".join(str(player.get(x) or "").strip() for x in ("first_name", "last_name")).strip()).strip()
        row = {
            "captured_at": captured_at, "availability_as_of": day, "source": SOURCE,
            "sleeper_id": sid, "full_name": name or None, "team": team or None,
            "position_model": pos or None,
        }
        if pos not in OFFENSIVE_POSITIONS:
            row["source_position"] = player.get("position")
            row["fantasy_positions"] = sorted(fantasy)
        for field in FIELDS:
            if player.get(field) is not None:
                row[field] = player[field]
        rows.append(row)
    rows.sort(key=lambda row: (row["position_model"] or "", row["team"] or "", row["sleeper_id"]))
    return rows


def coverage(rows: list[dict]) -> dict:
    result = {}
    for group in ("OFFENSE", "IDP", "KICKER"):
        selected = [row for row in rows if group_for(row) == group]
        result[group] = {
            "rows": len(selected), "rows_with_team": sum(row.get("team") is not None for row in selected),
            "rows_with_injury_status": sum(bool(row.get("injury_status")) for row in selected),
            "non_null_field_counts": {field: sum(field in row for row in selected) for field in FIELDS},
        }
    return result


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False).encode("utf-8")


def compressed_first_write(path: Path, content: bytes) -> None:
    with path.open("xb") as handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as archive:
            archive.write(content)


def validate_capture(path: Path) -> dict:
    meta = json.loads(Path(str(path) + ".meta.json").read_text(encoding="utf-8"))
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if len(rows) != meta.get("rows"):
        raise ValueError("Availability row count does not match sidecar")
    if meta.get("capture_contract") != CONTRACT:
        if meta.get('source_archive'):
            raise ValueError('Unknown source-backed availability capture contract')
        return meta  # Existing legacy captures are preserved, never upgraded.
    source = path.parent / meta["source_archive"]
    if source.parent != path.parent or source.name != meta["source_archive"]:
        raise ValueError("Invalid source archive path")
    if sha256(path.read_bytes()).hexdigest() != meta["snapshot_sha256"] or sha256(source.read_bytes()).hexdigest() != meta["source_archive_sha256"]:
        raise ValueError("Availability archive hash mismatch")
    with gzip.open(source, "rt", encoding="utf-8") as handle:
        envelope = json.load(handle)
    if envelope["observed_at"] != meta["captured_at"] or envelope["endpoint"] != URL:
        raise ValueError("Availability source binding mismatch")
    if sha256(canonical(envelope["payload"])).hexdigest() != meta["source_payload_sha256"]:
        raise ValueError("Availability source payload hash mismatch")
    if rows != compact(envelope["payload"], meta["captured_at"], meta["availability_as_of"]):
        raise ValueError("Availability rows do not match captured source")
    if meta["coverage"] != coverage(rows) or meta["position_counts"] != dict(sorted(Counter(row["position_model"] or "UNKNOWN" for row in rows).items())):
        raise ValueError("Availability coverage does not match rows")
    if meta["season"] != football_season(meta["captured_at"]) or meta["availability_as_of"] != parse_time(meta["captured_at"]).date().isoformat():
        raise ValueError("Availability date/season binding mismatch")
    if meta['positions'] != sorted(POSITIONS) or meta['source_player_count'] != len(envelope['payload']) or meta['rows_with_injury_status'] != sum(bool(row.get('injury_status')) for row in rows):
        raise ValueError('Availability source scope/count mismatch')
    return meta


def target_path(root: Path, captured: str) -> Path:
    day = parse_time(captured).date().isoformat()
    path = root / str(football_season(captured)) / f"availability_{day}.jsonl.gz"
    if path.exists() and validate_capture(path).get("capture_contract") != CONTRACT:
        path = path.with_name(f"availability_{day}_expanded-v1.jsonl.gz")
    return path


def capture(*, output_root: Path, fixture: bool = False, automatic: bool = False, as_of: str | None = None) -> dict:
    before = now_iso()
    if as_of is not None:
        date.fromisoformat(as_of)
        if not fixture and as_of != parse_time(before).date().isoformat():
            raise ValueError("Live availability cannot be backdated or future-dated")
    if fixture and as_of:
        before = as_of + "T08:29:00+00:00"
    if automatic and not automatic_capture_allowed(before):
        return {"capture_status": "SKIPPED_OUTSIDE_SEASON", "capture_allowed": False}
    path = target_path(output_root, before)
    if path.exists():
        return {**validate_capture(path), "capture_status": "EXISTS", "snapshot_path": str(path)}
    raw = fixture_players() if fixture else fetch_players()
    captured = before if fixture else now_iso()  # observation after response
    if automatic and not automatic_capture_allowed(captured):
        return {"capture_status": "SKIPPED_OUTSIDE_SEASON", "capture_allowed": False}
    path = target_path(output_root, captured)
    if path.exists():
        return {**validate_capture(path), "capture_status": "EXISTS", "snapshot_path": str(path)}
    day = parse_time(captured).date().isoformat()
    rows = compact(raw, captured, day)
    if not rows:
        raise ValueError("Availability snapshot produced zero eligible individual players")
    path.parent.mkdir(parents=True, exist_ok=True)
    source = path.with_name(path.name.removesuffix(".jsonl.gz") + ".source.json.gz")
    compressed_first_write(source, canonical({"schema": "fie-availability-provider-response-v1", "endpoint": URL, "observed_at": captured, "payload": raw}))
    compressed_first_write(path, b"".join(canonical(row) + b"\n" for row in rows))
    meta = {
        "capture_contract": CONTRACT, "captured_at": captured, "availability_as_of": day,
        "season": football_season(captured), "source": SOURCE, "rows": len(rows),
        "positions": sorted(POSITIONS), "position_counts": dict(sorted(Counter(row["position_model"] or "UNKNOWN" for row in rows).items())),
        "coverage": coverage(rows), "source_player_count": len(raw),
        "rows_with_injury_status": sum(bool(row.get("injury_status")) for row in rows),
        "immutable_first_write": True, "capture_mode": "FIXTURE" if fixture else "AUTOMATIC" if automatic else "MANUAL",
        "snapshot_sha256": sha256(path.read_bytes()).hexdigest(), "source_archive": source.name,
        "source_archive_sha256": sha256(source.read_bytes()).hexdigest(), "source_payload_sha256": sha256(canonical(raw)).hexdigest(),
        "semantics": "observed provider fields; missing is unknown; no historical reconstruction or playing-probability inference",
        "point_in_time_metadata": {
            "schema": "fie-point-in-time-source-metadata-v1", "capture_intent": "prospective_availability",
            "source_endpoint": URL, "source_release_identifier": None, "source_revision_identifier": None,
            "revision_metadata_status": "NOT_EXPOSED_BY_PROVIDER",
            "as_of_semantics": "UTC observation date; source response retained; no backdating; season follows September-January Berlin window",
            "release_cadence": "daily scheduled prospective capture, September through January 10",
        },
    }
    with Path(str(path) + ".meta.json").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(meta, indent=2, allow_nan=False) + "\n")
    validate_capture(path)
    return {**meta, "capture_status": "CREATED", "snapshot_path": str(path)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="data/research/availability/sleeper")
    parser.add_argument("--as-of", help="UTC date; live calls accept only today's date; fixtures permit historical dates")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--automatic", action="store_true")
    parser.add_argument("--schedule-check", action="store_true")
    parser.add_argument("--output-index")
    args = parser.parse_args(argv)
    if args.schedule_check:
        print(f"capture_allowed={str(automatic_capture_allowed(now_iso())).lower()}")
        return
    result = capture(output_root=Path(args.output_root), fixture=args.fixture, automatic=args.automatic, as_of=args.as_of)
    if args.output_index:
        output = Path(args.output_index)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"PASS availability status={result['capture_status']} rows={result.get('rows', 0)} coverage={json.dumps(result.get('coverage', {}), separators=(',', ':'))}")


if __name__ == "__main__":
    main()
