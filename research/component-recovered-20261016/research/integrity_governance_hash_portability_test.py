#!/usr/bin/env python3
"""Governance artifact hashes must match Git/Cloudflare on every host OS."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

from fie_governance import sha256_file

ROOT = Path(__file__).resolve().parents[1]
LEAGUES = ROOT / "data/research/leagues"

spec = importlib.util.spec_from_file_location("fie_build_dist_portability", ROOT / "tools/build_dist.py")
dist_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dist_builder)


with tempfile.TemporaryDirectory() as td:
    lf = Path(td) / "lf.json"
    crlf = Path(td) / "crlf.json"
    lf.write_bytes(b'{\n  "ok": true\n}\n')
    crlf.write_bytes(b'{\r\n  "ok": true\r\n}\r\n')
    assert sha256_file(lf) == sha256_file(crlf), "JSON governance hashes must be newline-portable"
    assert sha256_file(lf) == hashlib.sha256(lf.read_bytes()).hexdigest()
    original = crlf.read_bytes()
    served = Path(td) / "served.json"
    dist_builder.copy(crlf, served, governed_json=True)
    expected = sha256_file(lf)
    assert hashlib.sha256(served.read_bytes()).hexdigest() == expected, "browser byte hash must match source governance after a CRLF checkout"
    assert served.read_bytes() == lf.read_bytes(), "governed copy must retain the authenticated LF JSON representation"
    assert crlf.read_bytes() == original, "deploy copy must not mutate source evidence"
    plain = Path(td) / "plain.json"
    dist_builder.copy(crlf, plain)
    assert plain.read_bytes() == original, "unrelated manifest/config copies remain byte-exact"
    served.write_bytes(served.read_bytes().replace(b"true", b"false"))
    assert hashlib.sha256(served.read_bytes()).hexdigest() != expected, "JSON content changes must still fail the governed digest"

checked = 0
for governance_path in sorted(LEAGUES.glob("*/governance/active_release.json")):
    governance = json.loads(governance_path.read_text(encoding="utf-8"))
    lineage = governance.get("model_lineage") or {}
    paths = lineage.get("artifact_paths") or {}
    hashes = lineage.get("artifact_sha256") or {}
    for key, ref in paths.items():
        artifact = Path(ref)
        if artifact.is_absolute():
            marker = "/Fantasy-Intelligence/"
            text = artifact.as_posix()
            assert marker in text, f"unscoped absolute governance path: {artifact}"
            artifact = ROOT / text.split(marker, 1)[1]
        else:
            artifact = ROOT / artifact
        assert artifact.exists(), f"missing governed artifact: {artifact}"
        assert hashes.get(key) == sha256_file(artifact), f"stale portable governance hash: {governance_path.parent.parent.name} {key}"
        checked += 1

assert checked >= 23 * 4, f"expected at least four governed artifacts for 23 active leagues, got {checked}"
print(f"PASS portable governance hashes across {checked} league artifacts")
