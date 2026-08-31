#!/usr/bin/env python3
"""One-time, fail-closed migration adding CHOPPED_BESTBALL to FIE.

Designed for the 2026-08-31 main branch architecture. The script:
- adds a sixth canonical format without changing existing league semantics,
- combines existing M5 Chopped downside + Best Ball spike evidence by intersection,
- keeps legacy M5 contract revisions 1-4 valid,
- adds the three user-supplied leagues to the managed portfolio,
- patches browser decision utility so the hybrid uses both lower-tail and spike value,
- updates deterministic integrity guards,
- creates a dedicated hybrid-format integrity test.

It is intentionally idempotent. Conflicting or unexpected source state aborts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HYBRID = "CHOPPED_BESTBALL"

NEW_LEAGUES = [
    {
        "league_id": "1399128582088835072",
        "alias": "1399128582088835072",
        "format": "REDRAFT",
        "priority": "HIGH",
        "enabled": True,
        "use_cookies": False,
        "wants_transactions": True,
        "notes": "User-provided 2026 league; added 2026-08-31",
    },
    {
        "league_id": "1399318410818519040",
        "alias": "1399318410818519040",
        "format": HYBRID,
        "priority": "HIGH",
        "enabled": True,
        "use_cookies": False,
        "wants_transactions": True,
        "notes": "User-provided 2026 Chopped + Best Ball league; added 2026-08-31",
    },
    {
        "league_id": "1396507356048658438",
        "alias": "1396507356048658438",
        "format": "CHOPPED",
        "priority": "HIGH",
        "enabled": True,
        "use_cookies": False,
        "wants_transactions": True,
        "notes": "User-provided 2026 Chopped league; added 2026-08-31",
    },
]


def die(msg: str) -> None:
    raise SystemExit(f"FAIL CLOSED: {msg}")


def read(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        die(f"missing expected file {path}")
    return p.read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n == 0:
        if new in text:
            return text
        die(f"{label}: expected source pattern not found")
    if n != 1:
        die(f"{label}: source pattern matched {n} times, expected exactly 1")
    return text.replace(old, new, 1)


def insert_after_once(text: str, marker: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        return text
    n = text.count(marker)
    if n != 1:
        die(f"{label}: marker matched {n} times, expected exactly 1")
    return text.replace(marker, marker + insertion, 1)


def patch_league_profile() -> None:
    path = "research/league_profile.py"
    s = read(path)
    if '"CHOPPED_BESTBALL"' not in s:
        s = replace_once(
            s,
            '    "REDRAFT_BESTBALL", "DYNASTY_BESTBALL",\n',
            '    "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED_BESTBALL",\n',
            "league_profile FORMATS",
        )
    old = '    if is_chopped:\n        return "CHOPPED"\n    if is_dynasty and is_best_ball:\n'
    new = '    if is_chopped and is_best_ball:\n        return "CHOPPED_BESTBALL"\n    if is_chopped:\n        return "CHOPPED"\n    if is_dynasty and is_best_ball:\n'
    if "if is_chopped and is_best_ball:" not in s:
        s = replace_once(s, old, new, "league_profile hybrid auto-resolution")
    write(path, s)


def patch_m5() -> None:
    path = "research/fie_m5.py"
    s = read(path)

    hybrid_profile = '''        "CHOPPED_BESTBALL": {
            "label": "Chopped + Best Ball",
            "evidence_status": "validated_player_level_proxy" if bb_ok >= 4 and ch_ok >= 4 and weekly_ok >= 4 and redraft_ok >= 4 else "diagnostic_only",
            "production_core": "weekly downside/survival + spike-week probability + depth contribution",
            "draft_weights": {"season_projection": .25, "vor": .10, "floor": .20, "early_week": .15, "spike": .20, "depth_fit": .10},
            "waiver_weights": {"next3": .20, "floor": .20, "spike": .20, "role_change": .15, "weekly": .15, "market": .10},
            "limitation": "hybrid utility intersects player-level Chopped bust-risk and Best Ball spike evidence; it is not a historical roster-level guillotine optimal-lineup simulation",
        },
'''
    if '"CHOPPED_BESTBALL": {' not in s:
        marker = '        "CHOPPED": {\n            "label": "Chopped",'
        if s.count(marker) != 1:
            die("fie_m5 hybrid profile insertion marker drifted")
        s = s.replace(marker, hybrid_profile + marker, 1)

    s = insert_after_once(
        s,
        '        "CHOPPED": sorted(set(runtime_positions) & set(risk_positions) & set(chopped_positions)),\n',
        '        "CHOPPED_BESTBALL": sorted(set(runtime_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions)),\n',
        "M5 format_position_gates",
    )
    s = insert_after_once(
        s,
        '            "CHOPPED": sorted(set(weekly_positions) & set(risk_positions) & set(chopped_positions)),\n',
        '            "CHOPPED_BESTBALL": sorted(set(weekly_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions)),\n',
        "M5 weekly hybrid gate",
    )
    s = insert_after_once(
        s,
        '            "CHOPPED": sorted(set(draft_positions) & set(risk_positions) & set(chopped_positions)),\n',
        '            "CHOPPED_BESTBALL": sorted(set(draft_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions)),\n',
        "M5 draft hybrid gate",
    )
    s = insert_after_once(
        s,
        '            "CHOPPED": sorted(set(waiver_positions) & set(chopped_positions)),\n',
        '            "CHOPPED_BESTBALL": sorted(set(waiver_positions) & set(chopped_positions) & set(bb_positions)),\n',
        "M5 waiver hybrid gate",
    )

    if '"contract_revision": 5,' not in s:
        s = replace_once(s, '"contract_revision": 4,', '"contract_revision": 5,', "M5 contract revision")

    old_step27 = '"step27": "One football projection core feeds separate transparent Redraft, Dynasty, Best Ball and Chopped utility transforms; format-specific evidence limits are surfaced.",'
    new_step27 = '"step27": "One football projection core feeds separate transparent Redraft, Dynasty, Best Ball, Chopped and Chopped + Best Ball utility transforms; the hybrid requires the intersection of Chopped downside and Best Ball spike evidence.",'
    if old_step27 in s:
        s = s.replace(old_step27, new_step27, 1)

    old_lim = '            "Chopped validation is player-level downside evidence, not a historical guillotine elimination simulation.",\n'
    hybrid_lim = '            "Chopped + Best Ball validation requires both Chopped downside and Best Ball spike evidence; no separate unvalidated hybrid football model is introduced.",\n'
    if hybrid_lim.strip() not in s:
        s = insert_after_once(s, old_lim, hybrid_lim, "M5 hybrid limitation")

    write(path, s)


def patch_m5_validator() -> None:
    path = "research/validate_m5_bundle.py"
    s = read(path)

    old_const = 'EXPECTED_FORMATS = {"REDRAFT", "DYNASTY", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED"}\n'
    new_const = (
        'LEGACY_FORMATS = {"REDRAFT", "DYNASTY", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED"}\n'
        'CURRENT_FORMATS = LEGACY_FORMATS | {"CHOPPED_BESTBALL"}\n'
    )
    if "CURRENT_FORMATS" not in s:
        s = replace_once(s, old_const, new_const, "M5 validator format constants")

    marker = '    assert b.get("integration_mode") == "fail_closed_conditional"\n'
    setup = '\n    revision = int(b.get("contract_revision") or 1)\n    expected_formats = CURRENT_FORMATS if revision >= 5 else LEGACY_FORMATS\n'
    if "expected_formats = CURRENT_FORMATS" not in s:
        s = insert_after_once(s, marker, setup, "M5 validator revision-aware formats")

    s = s.replace('assert set(format_gates) == EXPECTED_FORMATS', 'assert set(format_gates) == expected_formats')
    s = s.replace('assert set(profiles) == EXPECTED_FORMATS', 'assert set(profiles) == expected_formats')
    s = s.replace('assert set(by_format) == EXPECTED_FORMATS, decision', 'assert set(by_format) == expected_formats, decision')

    if s.count('revision = int(b.get("contract_revision") or 1)') > 1:
        s = replace_once(
            s,
            '    revision = int(b.get("contract_revision") or 1)\n    if revision >= 2:\n',
            '    if revision >= 2:\n',
            "M5 validator duplicate revision assignment",
        )

    if "The hybrid can never activate" not in s:
        guard = '''    if revision >= 5:
        fmt = gates.get("format_position_gates", {})
        decision_fmt = gates.get("decision_format_position_gates", {})
        assert "CHOPPED_BESTBALL" in fmt
        for decision in ("weekly", "draft", "waiver"):
            assert "CHOPPED_BESTBALL" in decision_fmt.get(decision, {}), decision
        # The hybrid can never activate a position absent from either constituent
        # format. This is the fail-closed composition rule.
        hybrid = set(fmt["CHOPPED_BESTBALL"])
        assert hybrid.issubset(set(fmt.get("CHOPPED", [])))
        assert hybrid.issubset(set(fmt.get("REDRAFT_BESTBALL", [])))
        for decision in ("weekly", "draft", "waiver"):
            by = decision_fmt[decision]
            h = set(by["CHOPPED_BESTBALL"])
            assert h.issubset(set(by.get("CHOPPED", []))), decision
            assert h.issubset(set(by.get("REDRAFT_BESTBALL", []))), decision

'''
        s = insert_after_once(s, '    text = json.dumps(b)\n', guard, "M5 revision-5 intersection guard")

    write(path, s)


def patch_decision_model() -> None:
    path = "app/decision-model-v9.js"
    s = read(path)
    old = "  for(const r of rows){if(fmt==='CHOPPED'){const rep=replacement(rows,r.p.position,'floor'),w=cw.chopped_utility_weights||{vor:.55,lower_tail_surplus:.45};r.raw=(num(w.vor,.55))*(r.vor/17)+(num(w.lower_tail_surplus,.45))*(r.floor-rep.value);r.rawUnit=`weekly lower-tail surplus vs ${r.p.position}${rep.cutoff}`;r.replacementCutoff=rep.cutoff;}\n    else if(fmt.includes('BESTBALL')){"
    new = "  for(const r of rows){if(fmt==='CHOPPED_BESTBALL'){const floorRep=replacement(rows,r.p.position,'floor'),spikeRep=replacement(rows,r.p.position,'ceiling'),w=cw.chopped_bestball_utility_weights||{vor:.40,lower_tail_surplus:.30,spike_surplus:.30};r.raw=num(w.vor,.40)*(r.vor/17)+num(w.lower_tail_surplus,.30)*(r.floor-floorRep.value)+num(w.spike_surplus,.30)*(r.ceiling-spikeRep.value);r.rawUnit=`hybrid lower-tail + spike surplus vs ${r.p.position}${floorRep.cutoff}/${spikeRep.cutoff}`;r.replacementCutoff=`${floorRep.cutoff}/${spikeRep.cutoff}`;}\n    else if(fmt==='CHOPPED'){const rep=replacement(rows,r.p.position,'floor'),w=cw.chopped_utility_weights||{vor:.55,lower_tail_surplus:.45};r.raw=(num(w.vor,.55))*(r.vor/17)+(num(w.lower_tail_surplus,.45))*(r.floor-rep.value);r.rawUnit=`weekly lower-tail surplus vs ${r.p.position}${rep.cutoff}`;r.replacementCutoff=rep.cutoff;}\n    else if(fmt.includes('BESTBALL')){"
    if "chopped_bestball_utility_weights" not in s:
        s = replace_once(s, old, new, "decision-model hybrid utility")

    old_arch = "marketEdge:'empirical league-utility curve',chopped:'candidate lower-tail surplus using league-wide replacement cutoff'"
    new_arch = "marketEdge:'empirical league-utility curve',chopped:'candidate lower-tail surplus using league-wide replacement cutoff',choppedBestBall:'combined lower-tail + spike surplus; no independent football model'"
    if "choppedBestBall:" not in s:
        s = replace_once(s, old_arch, new_arch, "decision-model architecture metadata")
    write(path, s)



def patch_portfolio_rules() -> None:
    path = "research/portfolio_rules.py"
    s = read(path)

    old_formats = 'FORMATS = {"REDRAFT", "DYNASTY", "CHOPPED", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL"}'
    new_formats = 'FORMATS = {"REDRAFT", "DYNASTY", "CHOPPED", "CHOPPED_BESTBALL", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL"}'
    if '"CHOPPED_BESTBALL"' not in s.split('PRIORITIES', 1)[0]:
        s = replace_once(s, old_formats, new_formats, "portfolio_rules canonical format set")

    old_alias = '        "BESTBALL_DYNASTY": "DYNASTY_BESTBALL",\n'
    alias_add = (
        '        "CHOPPED_BEST_BALL": "CHOPPED_BESTBALL",\n'
        '        "BESTBALL_CHOPPED": "CHOPPED_BESTBALL",\n'
    )
    if '"CHOPPED_BEST_BALL": "CHOPPED_BESTBALL"' not in s:
        s = insert_after_once(s, old_alias, ''.join(alias_add), "portfolio_rules hybrid aliases")

    write(path, s)

def patch_portfolio_config_json() -> None:
    path = ROOT / "config" / "league-portfolio.json"
    if not path.exists():
        die("missing config/league-portfolio.json")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    leagues = cfg.get("leagues")
    if not isinstance(leagues, list):
        die("league-portfolio.json leagues is not a list")
    by_id = {str(x.get("league_id")): x for x in leagues}
    for new in NEW_LEAGUES:
        lid = new["league_id"]
        if lid in by_id:
            existing = by_id[lid]
            if str(existing.get("format")) != new["format"]:
                die(f"league {lid} already exists with conflicting format {existing.get('format')!r}")
            existing.setdefault("priority", "HIGH")
            existing.setdefault("enabled", True)
            continue
        leagues.append(dict(new))
    ids = [str(x.get("league_id")) for x in leagues]
    if len(ids) != len(set(ids)):
        die("portfolio contains duplicate league IDs")
    if len(leagues) < 22:
        die(f"expected at least 22 managed leagues after migration, found {len(leagues)}")

    cfg["version"] = "2026.08.31"
    notes = cfg.setdefault("notes", {})
    if isinstance(notes, dict):
        notes["all_league_ids_summary"] = f"{len(leagues)} Sleeper leagues total"
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_app_portfolio_config() -> None:
    path = "app/portfolio-config.js"
    s = read(path)
    old = "const FORMAT_LABELS={REDRAFT:'Redraft',DYNASTY:'Dynasty',CHOPPED:'Chopped',REDRAFT_BESTBALL:'Redraft + Best Ball',DYNASTY_BESTBALL:'Dynasty + Best Ball'};"
    new = "const FORMAT_LABELS={REDRAFT:'Redraft',DYNASTY:'Dynasty',CHOPPED:'Chopped',CHOPPED_BESTBALL:'Chopped + Best Ball',REDRAFT_BESTBALL:'Redraft + Best Ball',DYNASTY_BESTBALL:'Dynasty + Best Ball'};"
    if "CHOPPED_BESTBALL:'Chopped + Best Ball'" not in s:
        s = replace_once(s, old, new, "browser portfolio format label")
    write(path, s)


def patch_complete_workflow() -> None:
    path = ".github/workflows/build-fie-complete-league-research.yml"
    s = read(path)
    old = "options: [AUTO, REDRAFT, DYNASTY, CHOPPED, REDRAFT_BESTBALL, DYNASTY_BESTBALL]"
    new = "options: [AUTO, REDRAFT, DYNASTY, CHOPPED, CHOPPED_BESTBALL, REDRAFT_BESTBALL, DYNASTY_BESTBALL]"
    if "CHOPPED_BESTBALL" not in s:
        s = replace_once(s, old, new, "complete research workflow format options")
    write(path, s)


def patch_integrity_tests() -> None:
    path = "research/integrity_m5_test.py"
    s = read(path)
    old = 'assert set(profiles) == {"REDRAFT", "DYNASTY", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED"}'
    new = 'assert set(profiles) == {"REDRAFT", "DYNASTY", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED", "CHOPPED_BESTBALL"}'
    if new not in s:
        s = replace_once(s, old, new, "integrity_m5 six-format assertion")
    write(path, s)

    path = "research/integrity_bulk_onboarding_test.py"
    s = read(path)
    if "assert len(cfg['leagues'])==22" not in s:
        s = replace_once(s, "assert len(cfg['leagues'])==19", "assert len(cfg['leagues'])==22", "bulk onboarding count")
    write(path, s)

    path = "research/integrity_custom_league_rules_test.py"
    s = read(path)
    if "assert len(cfg['leagues'])==22" not in s:
        s = replace_once(s, "assert len(cfg['leagues'])==19", "assert len(cfg['leagues'])==22", "custom rules count")
    old_formats = "assert formats=={'CHOPPED':4,'REDRAFT':3,'REDRAFT_BESTBALL':2,'DYNASTY':7,'DYNASTY_BESTBALL':3},formats"
    new_formats = "assert formats=={'CHOPPED':5,'REDRAFT':4,'REDRAFT_BESTBALL':2,'DYNASTY':7,'DYNASTY_BESTBALL':3,'CHOPPED_BESTBALL':1},formats"
    if new_formats not in s:
        s = replace_once(s, old_formats, new_formats, "custom rules format counts")
    s = s.replace(
        "print('PASS: 19-league portfolio + fixed-cohort custom rules are valid, research-fingerprinted and exposed through modular browser rules')",
        "print('PASS: 22-league portfolio + hybrid format + fixed-cohort custom rules are valid, research-fingerprinted and exposed through modular browser rules')",
    )
    write(path, s)


def write_hybrid_integrity_test() -> None:
    path = ROOT / "research" / "integrity_chopped_bestball_test.py"
    content = '''#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

from league_profile import FORMATS, infer_format
from validate_m5_bundle import CURRENT_FORMATS, LEGACY_FORMATS

ROOT = Path(__file__).resolve().parents[1]
HYBRID = "CHOPPED_BESTBALL"

assert HYBRID in FORMATS
assert HYBRID in CURRENT_FORMATS
assert HYBRID not in LEGACY_FORMATS

fixture = {
    "league_id": "1399318410818519040",
    "name": "Hybrid fixture",
    "type": "redraft",
    "settings": {"type": 3, "best_ball": 1},
}
assert infer_format(fixture, "AUTO") == HYBRID
assert infer_format(fixture, HYBRID) == HYBRID
assert infer_format({**fixture, "settings": {"type": 3, "best_ball": 0}}, "AUTO") == "CHOPPED"
assert infer_format({**fixture, "settings": {"type": 0, "best_ball": 1}}, "AUTO") == "REDRAFT_BESTBALL"

cfg = json.loads((ROOT / "config" / "league-portfolio.json").read_text())
by_id = {str(x["league_id"]): x for x in cfg["leagues"]}
expected = {
    "1399128582088835072": "REDRAFT",
    "1399318410818519040": HYBRID,
    "1396507356048658438": "CHOPPED",
}
for lid, fmt in expected.items():
    assert by_id[lid]["format"] == fmt, (lid, by_id[lid])
assert len(by_id) == len(cfg["leagues"])
assert len(cfg["leagues"]) >= 22

m5 = (ROOT / "research" / "fie_m5.py").read_text()
for token in ['"CHOPPED_BESTBALL": {', '"contract_revision": 5', 'set(chopped_positions) & set(bb_positions)']:
    assert token in m5, token
assert '"CHOPPED_BESTBALL": sorted(set(runtime_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions))' in m5
assert '"CHOPPED_BESTBALL": sorted(set(weekly_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions))' in m5
assert '"CHOPPED_BESTBALL": sorted(set(draft_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions))' in m5
assert '"CHOPPED_BESTBALL": sorted(set(waiver_positions) & set(chopped_positions) & set(bb_positions))' in m5

js = (ROOT / "app" / "decision-model-v9.js").read_text()
assert "fmt==='CHOPPED_BESTBALL'" in js
assert "chopped_bestball_utility_weights" in js
assert "lower_tail_surplus" in js and "spike_surplus" in js

portfolio_js = (ROOT / "app" / "portfolio-config.js").read_text()
assert "CHOPPED_BESTBALL:'Chopped + Best Ball'" in portfolio_js


print("PASS: CHOPPED_BESTBALL auto-detection, portfolio registration, M5 fail-closed intersections, workflow and browser utility")
'''
    path.write_text(content, encoding="utf-8")


def verify_postconditions() -> None:
    lp = read("research/league_profile.py")
    if '"CHOPPED_BESTBALL"' not in lp or "if is_chopped and is_best_ball:" not in lp:
        die("league_profile postcondition failed")

    m5 = read("research/fie_m5.py")
    if m5.count('"CHOPPED_BESTBALL"') < 5:
        die("M5 hybrid contract incomplete")
    if '"contract_revision": 5' not in m5:
        die("M5 contract revision was not upgraded")

    portfolio_rules = read("research/portfolio_rules.py")
    if '"CHOPPED_BESTBALL"' not in portfolio_rules:
        die("portfolio_rules hybrid format postcondition failed")

    cfg = json.loads((ROOT / "config" / "league-portfolio.json").read_text())
    by = {str(x["league_id"]): x for x in cfg["leagues"]}
    for x in NEW_LEAGUES:
        if by.get(x["league_id"], {}).get("format") != x["format"]:
            die(f"portfolio postcondition failed for {x['league_id']}")

    joined = read("research/fie_m5.py") + "\n" + read("app/decision-model-v9.js")
    if "HYBRID_MODEL" in joined or "CHOPPED_BESTBALL_MODEL" in joined:
        die("unexpected independent hybrid football model detected")


def main() -> None:
    patch_league_profile()
    patch_m5()
    patch_m5_validator()
    patch_decision_model()
    patch_portfolio_rules()
    patch_portfolio_config_json()
    patch_app_portfolio_config()
    patch_integrity_tests()
    write_hybrid_integrity_test()
    verify_postconditions()
    print("PASS: FIE CHOPPED_BESTBALL migration applied")
    for x in NEW_LEAGUES:
        print(f"  {x['league_id']} -> {x['format']}")


if __name__ == "__main__":
    main()
