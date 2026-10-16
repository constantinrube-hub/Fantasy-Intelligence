#!/usr/bin/env python3
"""Controlled implementation Tranche 0 baseline harness.

This file intentionally changes no FIE model/runtime semantics.
It verifies that the implementation branch starts from the audited baseline,
runs the existing canonical release build plus important tests outside the
direct release gate, and writes reproducible baseline artifacts for Tranche 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "config" / "tranche0-baseline.json"


def run(cmd: list[str], *, check: bool = True, capture: bool = True) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=capture,
    )
    result = {
        "cmd": cmd,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": proc.stdout if capture else "",
        "stderr": proc.stderr if capture else "",
    }
    if check and proc.returncode != 0:
        if capture:
            sys.stdout.write(proc.stdout or "")
            sys.stderr.write(proc.stderr or "")
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}")
    return result


def git(*args: str, check: bool = True) -> str:
    r = run(["git", *args], check=check)
    return (r["stdout"] or "").strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def priority(v: str | None) -> int:
    return {
        "VERY_HIGH": 5,
        "HIGH": 4,
        "MEDIUM": 3,
        "LOW": 2,
        "VERY_LOW": 1,
    }.get(str(v or "").upper(), 0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="artifacts/tranche0")
    args = ap.parse_args()

    cfg = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    baseline_sha = cfg["baseline_commit"]
    baseline_tree = cfg["baseline_tree"]
    allowed = set(cfg["allowed_tranche0_changes"])

    head = git("rev-parse", "HEAD")
    head_tree = git("rev-parse", "HEAD^{tree}")
    baseline_actual_tree = git("rev-parse", f"{baseline_sha}^{{tree}}")
    if baseline_actual_tree != baseline_tree:
        raise RuntimeError(
            f"baseline tree mismatch: expected {baseline_tree}, got {baseline_actual_tree}"
        )

    run(["git", "merge-base", "--is-ancestor", baseline_sha, head])

    changed = [
        x for x in git("diff", "--name-only", f"{baseline_sha}..HEAD").splitlines()
        if x.strip()
    ]
    unexpected = sorted(set(changed) - allowed)
    if unexpected:
        raise RuntimeError(
            "Tranche 0 branch contains non-baseline source changes:\n- "
            + "\n- ".join(unexpected)
        )

    ref_name = os.environ.get("GITHUB_REF_NAME")
    if ref_name and ref_name != cfg["implementation_branch"]:
        raise RuntimeError(
            f"workflow must run on {cfg['implementation_branch']}, got {ref_name}"
        )

    registry_path = ROOT / "data" / "research" / "leagues" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leagues = registry.get("leagues", {})
    enabled = {
        str(k): v for k, v in leagues.items()
        if isinstance(v, dict) and v.get("enabled") is True
    }

    by_format: dict[str, list[dict]] = {}
    for lid, meta in enabled.items():
        fmt = str(meta.get("format") or "UNKNOWN").upper()
        by_format.setdefault(fmt, []).append({"league_id": lid, **meta})

    missing_formats = [
        fmt for fmt in cfg["expected_formats"]
        if fmt not in by_format
    ]
    if missing_formats:
        raise RuntimeError(f"enabled registry is missing formats: {missing_formats}")

    reps = {}
    for fmt, lid in cfg["representative_leagues"].items():
        meta = enabled.get(lid)
        if not meta:
            raise RuntimeError(f"representative league {lid} for {fmt} is not enabled")
        actual = str(meta.get("format") or "").upper()
        if actual != fmt:
            raise RuntimeError(
                f"representative league {lid}: expected {fmt}, registry says {actual}"
            )
        profile = ROOT / str(meta["profile_path"])
        if not profile.exists():
            raise RuntimeError(f"profile missing for {lid}: {profile}")
        reps[fmt] = {
            "league_id": lid,
            "league_name": meta.get("league_name"),
            "priority": meta.get("priority"),
            "format": actual,
            "profile_path": str(profile.relative_to(ROOT)),
            "profile_sha256": sha256(profile),
            "profile_fingerprint": meta.get("profile_fingerprint"),
            "scoring_signature": meta.get("scoring_signature"),
            "research_contract_revision": meta.get("research_contract_revision"),
        }

    format_summary = {}
    for fmt, rows in sorted(by_format.items()):
        rows_sorted = sorted(
            rows,
            key=lambda x: (-priority(x.get("priority")), x["league_id"])
        )
        format_summary[fmt] = {
            "count": len(rows),
            "league_ids": [x["league_id"] for x in rows_sorted],
        }

    checks = []

    # Canonical release build includes the full release gate.
    commands = [
        [sys.executable, "tools/release_build.py", "--mode", "personal"],
        [sys.executable, "research/integrity_chopped_bestball_test.py"],
        ["node", "research/integrity_cross_position_calibration_test.js"],
        ["node", "research/integrity_league_fast_switch_runtime_test.js"],
        [sys.executable, "research/integrity_fast_switch_artifacts_test.py", "--require-dist"],
        [sys.executable, "research/integrity_multileague_test.py"],
        [sys.executable, "research/integrity_market_archive_test.py"],
        [sys.executable, "research/test_league_profile.py"],
        [sys.executable, "research/integrity_v96_runtime_test.py"],
    ]

    failed = False
    for cmd in commands:
        result = run(cmd, check=False)
        checks.append(result)
        print(("PASS" if result["ok"] else "FAIL"), " ".join(cmd))
        if result["stdout"]:
            print(result["stdout"][-4000:])
        if result["stderr"]:
            print(result["stderr"][-4000:], file=sys.stderr)
        failed = failed or not result["ok"]

    release_gate_path = ROOT / "config" / "release-gate.json"
    release_gate = {}
    if release_gate_path.exists():
        release_gate = json.loads(release_gate_path.read_text(encoding="utf-8"))

    dist_status = git("status", "--porcelain", "--", "dist")
    dist_synced = not bool(dist_status.strip())
    if not dist_synced:
        failed = True
        print("FAIL committed dist/ changed after deterministic release build")
        print(dist_status)
    else:
        print("PASS committed dist/ matches deterministic release build")

    post_status = git("status", "--porcelain")
    report = {
        "schema": "fie-tranche0-baseline-result-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "implementation_branch": cfg["implementation_branch"],
        "baseline_commit": baseline_sha,
        "baseline_tree": baseline_tree,
        "head_commit": head,
        "head_tree": head_tree,
        "changes_vs_baseline": changed,
        "unexpected_changes_vs_baseline": unexpected,
        "enabled_league_count": len(enabled),
        "format_summary": format_summary,
        "representative_leagues": reps,
        "release_gate_status": release_gate.get("status"),
        "browser_preview_required": release_gate.get("browser_preview_required"),
        "dist_synced_after_release_build": dist_synced,
        "post_test_git_status": post_status.splitlines(),
        "checks": checks,
        "pass": (
            not failed
            and release_gate.get("status") == "DEPLOYABLE_SOURCE"
            and dist_synced
            and not unexpected
        ),
    }

    (out / "tranche0-baseline.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# FIE Controlled Implementation — Tranche 0 Baseline Result",
        "",
        f"- Baseline commit: `{baseline_sha}`",
        f"- Baseline tree: `{baseline_tree}`",
        f"- Harness HEAD: `{head}`",
        f"- Enabled leagues: **{len(enabled)}**",
        f"- Release gate: **{report['release_gate_status']}**",
        f"- Dist synchronized: **{dist_synced}**",
        f"- Overall: **{'PASS' if report['pass'] else 'FAIL'}**",
        "",
        "## Format inventory",
        "",
        "| Format | Count | Representative |",
        "|---|---:|---|",
    ]
    for fmt in cfg["expected_formats"]:
        lines.append(
            f"| {fmt} | {format_summary[fmt]['count']} | "
            f"`{reps[fmt]['league_id']}` — {reps[fmt]['league_name']} |"
        )
    lines += ["", "## Checks", ""]
    for c in checks:
        lines.append(
            f"- {'PASS' if c['ok'] else 'FAIL'} — `{' '.join(c['cmd'])}`"
        )
    lines += [
        "",
        "## Scope",
        "",
        "This is a characterization/freeze baseline only.",
        "No production model, threshold, runtime behavior or cleanup is changed by Tranche 0.",
    ]
    (out / "tranche0-baseline.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    if failed:
        return 1
    if release_gate.get("status") != "DEPLOYABLE_SOURCE":
        print(
            f"FAIL release gate status is {release_gate.get('status')!r}, "
            "expected DEPLOYABLE_SOURCE"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
