"""All-league scoring demand. Registration is not source or forecast certification."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PLAYER_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DL', 'LB', 'DB']

OFFENSE = {
    "pass_att": "passing_attempts", "pass_cmp": "passing_completions",
    "pass_yd": "passing_yards", "pass_td": "passing_touchdowns",
    "pass_int": "passing_interceptions", "pass_sack": "passing_sacks_charged",
    "pass_int_td": "passing_pick_sixes", "pass_fd": "passing_first_downs",
    "pass_2pt": "passing_two_point_conversions", "pass_cmp_40p": "passing_completions_40_plus",
    "pass_td_40p": "passing_touchdowns_40_plus", "pass_td_50p": "passing_touchdowns_50_plus",
    "rush_att": "rushing_attempts", "rush_yd": "rushing_yards",
    "rush_td": "rushing_touchdowns", "rush_fd": "rushing_first_downs",
    "rush_2pt": "rushing_two_point_conversions", "rush_40p": "rushes_40_plus",
    "rush_td_40p": "rushing_touchdowns_40_plus", "rush_td_50p": "rushing_touchdowns_50_plus",
    "rec": "receptions", "rec_yd": "receiving_yards", "rec_td": "receiving_touchdowns",
    "rec_fd": "receiving_first_downs", "rec_2pt": "receiving_two_point_conversions",
    "rec_40p": "receptions_40_plus", "rec_td_40p": "receiving_touchdowns_40_plus",
    "rec_td_50p": "receiving_touchdowns_50_plus", "bonus_rec_te": "receptions",
    "bonus_rush_td_qb": "rushing_touchdowns", "fum": "fumbles",
    "fum_lost": "fumbles_lost", "fum_rec_td": "offensive_fumble_recovery_touchdowns",
    "kr_yd": "kick_return_yards", "pr_yd": "punt_return_yards",
    "st_td": "individual_special_teams_touchdowns", "st_ff": "individual_special_teams_forced_fumbles",
    "st_fum_rec": "individual_special_teams_fumble_recoveries",
}
IDP = {
    "tkl": "tackles_total", "tkl_solo": "tackles_solo", "tkl_ast": "tackles_assisted",
    "tkl_loss": "tackles_for_loss", "sack": "sacks", "sack_yd": "sack_yards",
    "qb_hit": "quarterback_hits", "pass_def": "passes_defended",
    "int": "interceptions", "int_ret_yd": "interception_return_yards",
    "ff": "forced_fumbles", "fum_rec": "fumble_recoveries", "fum_ret_yd": "fumble_return_yards",
    "safe": "safeties", "blk_kick": "blocked_kicks", "def_td": "defensive_touchdowns",
}
DST = {
    "sack": "sacks", "sack_yd": "sack_yards", "int": "interceptions",
    "int_ret_yd": "interception_return_yards", "ff": "forced_fumbles",
    "fum_rec": "fumble_recoveries", "fum_ret_yd": "fumble_return_yards",
    "def_td": "defensive_touchdowns", "safe": "safeties", "blk_kick": "blocked_kicks",
    "blk_kick_ret_yd": "blocked_kick_return_yards", "def_4_and_stop": "fourth_down_stops",
    "def_pass_def": "passes_defended", "def_st_td": "special_teams_touchdowns",
    "def_st_ff": "special_teams_forced_fumbles", "def_st_fum_rec": "special_teams_fumble_recoveries",
    "def_kr_yd": "kick_return_yards", "def_pr_yd": "punt_return_yards",
    "fg_ret_yd": "field_goal_return_yards", "def_fg_ret_yd": "field_goal_return_yards",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value):
    if isinstance(value, bool):
        raise ValueError("COMPONENT_BOOLEAN_NUMERIC_VALUE")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("COMPONENT_NONFINITE_VALUE")
    return number


def matching_rule(key, contracts):
    for rule in contracts["scoring_rule_families"]:
        kind, pattern = rule["match"], rule["pattern"]
        if ((kind == "exact" and key == pattern) or
                (kind == "exact_set" and key in pattern) or
                (kind == "prefix" and key.startswith(pattern)) or
                (kind == "regex" and re.search(pattern, key, re.I))):
            return rule
    return None


def canonical(position, contracts):
    return contracts["position_aliases"].get(position, position)


def position_universe(slots, contracts):
    positions = set()
    for slot in slots:
        if slot not in contracts["roster_slots"]:
            raise ValueError("COMPONENT_UNKNOWN_ROSTER_SLOT:" + slot)
        positions.update(canonical(p, contracts) for p in contracts["roster_slots"][slot]["positions"])
    return positions


def mapping(key, contracts):
    rule = matching_rule(key, contracts)
    if not rule:
        raise ValueError("COMPONENT_UNKNOWN_SCORING_RULE:" + key)
    mode, unit, derived = "mean", "count", []
    bounds = None
    if key in OFFENSE:
        component = OFFENSE[key]
        if key.endswith("_yd"):
            unit = "yards"
    elif key.startswith("idp_") and key[4:] in IDP:
        component = "idp_" + IDP[key[4:]]
        if key.endswith("_yd"):
            unit = "yards"
    elif key in DST:
        component = "dst_" + DST[key]
        if key.endswith("_yd"):
            unit = "yards"
    elif re.fullmatch(r"bonus_(pass|rush|rec)_yd_\d+", key):
        component = "prob_" + key.removeprefix("bonus_")
        mode, unit = "probability", "probability"
        kind, lower = re.fullmatch(r"bonus_(pass|rush|rec)_yd_(\d+)", key).groups()
        lower = int(lower)
        upper = {("pass", 300): 399, ("rush", 100): 199, ("rec", 100): 199}.get((kind, lower))
        bounds = {"lower_inclusive": lower, "upper_inclusive": upper, "exclusive_game_yardage_band": True}
    elif re.fullmatch(r"(pts|yds)_allow_(\d+(_\d+|p)?)", key):
        component = "dst_prob_" + key
        mode, unit = "probability", "probability"
    elif re.fullmatch(r"(fgm|fgmiss)_(\d+(_\d+|p)?)", key):
        component = "kicker_" + key
        if key == "fgm_50p":
            derived = ["kicker_fgm_50_59", "kicker_fgm_60p"]
    elif key in {"fgm", "fgmiss", "fgm_yds", "xpm", "xpmiss"}:
        component = "kicker_" + key
        if key == "fgm_yds":
            unit = "yards"
    else:
        raise ValueError("COMPONENT_MAPPING_NOT_IMPLEMENTED:" + key)
    positions = sorted(canonical(p, contracts) for p in rule["positions"])
    # The app's position-limited relevance contract is preserved. Component
    # outcomes must also cover trick plays, two-way players, and ANY player's
    # fumbles/returns. Position premiums alone retain their specific role.
    if key in OFFENSE and key not in {'bonus_rec_te', 'bonus_rush_td_qb', 'pass_sack'}:
        positions = PLAYER_POSITIONS
    if key.startswith('bonus_') and bounds is not None:
        positions = PLAYER_POSITIONS
    return {
        "scoring_key": key, "component": component, "mode": mode, "unit": unit,
        "family": rule["id"], "entity": rule["entity"],
        "positions": positions,
        "app_contract_positions": sorted(canonical(p, contracts) for p in rule["positions"]),
        "applicability_basis": "RAW_PLAYER_STAT_WITH_POSITION_PREMIUM_EXCEPTIONS",
        "derived_from": derived, "event_bounds": bounds,
        "semantic_status": "REGISTERED_REQUIRES_SOURCE_AND_PROVIDER_REPLAY",
        "source_verified": False,
    }


def score_expected(scoring, position, means, probabilities, contracts):
    """Expected contribution arithmetic only; no model/source certification."""
    position = canonical(position, contracts)
    for prefix in ('prob_pass_yd_', 'prob_rush_yd_', 'prob_rec_yd_', 'dst_prob_pts_allow_', 'dst_prob_yds_allow_'):
        values = [finite(v) for k,v in probabilities.items() if k.startswith(prefix)]
        if any(v < 0 or v > 1 for v in values):
            raise ValueError('COMPONENT_PROBABILITY_OUT_OF_RANGE')
        if math.fsum(values) > 1 + 1e-9:
            raise ValueError('COMPONENT_EXCLUSIVE_PROBABILITY_SUM_EXCEEDS_ONE')
    if all(k in means for k in ('kicker_fgm_50p','kicker_fgm_50_59','kicker_fgm_60p')):
        if not math.isclose(finite(means['kicker_fgm_50p']),
                            finite(means['kicker_fgm_50_59'])+finite(means['kicker_fgm_60p']),abs_tol=1e-9):
            raise ValueError('COMPONENT_KICKER_DISTANCE_AGGREGATE_DISAGREEMENT')
    contributions, missing = [], []
    for key, weight in sorted(scoring.items()):
        weight = finite(weight)
        if weight == 0:
            continue
        rule = mapping(key, contracts)
        if position not in rule["positions"]:
            continue
        source = probabilities if rule["mode"] == "probability" else means
        component = rule["component"]
        if component in source:
            value = finite(source[component])
        elif rule["derived_from"] and all(k in source for k in rule["derived_from"]):
            value = math.fsum(finite(source[k]) for k in rule["derived_from"])
        else:
            missing.append({"scoring_key": key, "component": component})
            continue
        if rule["unit"] == "probability" and not 0 <= value <= 1:
            raise ValueError("COMPONENT_PROBABILITY_OUT_OF_RANGE")
        if rule["unit"] == "count" and value < 0:
            raise ValueError("COMPONENT_NEGATIVE_COUNT")
        contributions.append({"scoring_key": key, "component": component,
                              "expectation": value, "weight": weight, "points": weight * value})
    subtotal = math.fsum(row["points"] for row in contributions)
    return {"arithmetic_complete": not missing, "points": subtotal if not missing else None,
            "supported_subtotal": subtotal, "contributions": contributions, "missing": missing,
            "forecast_certified": False}


def build(root=ROOT):
    root = Path(root).resolve()
    contracts_path = root / "config/contracts/runtime-contracts.json"
    contracts = json.loads(contracts_path.read_text())
    registry_path = root / "data/research/leagues/registry.json"
    registry = json.loads(registry_path.read_text())["leagues"]
    rows, leagues, components, configured = [], [], {}, set()
    for league_id, entry in sorted(registry.items()):
        if entry.get("enabled") is not True:
            continue
        path = root / entry["profile_path"]
        if not path.resolve().is_relative_to(root):
            raise ValueError("COMPONENT_PROFILE_OUTSIDE_ROOT")
        profile = json.loads(path.read_text())
        if str(profile["league_id"]) != league_id:
            raise ValueError("COMPONENT_PROFILE_ID_MISMATCH")
        positions = position_universe(profile["roster_positions"], contracts)
        irrelevant = []
        required = []
        for key, weight in sorted(profile["scoring_settings"].items()):
            weight = finite(weight)
            if weight == 0:
                continue
            configured.add(key)
            rule = mapping(key, contracts)
            if not positions.intersection(rule["positions"]):
                irrelevant.append({"scoring_key": key, "weight": weight, "reason": "NO_ELIGIBLE_ENTITY_POSITION_IN_PROFILE"})
                continue
            required.append(key)
            components.setdefault(rule["component"], {k: rule[k] for k in ("component", "mode", "unit", "derived_from", "event_bounds")})
            rows.append({"league_id": league_id, "league_name": profile["league_name"],
                         "scoring_signature": profile["scoring_signature"], "weight": weight, **rule})
        leagues.append({"league_id": league_id, "league_name": profile["league_name"],
                        "profile_path": entry["profile_path"], "profile_sha256": digest(path),
                        "positions": sorted(positions), "required_scoring_keys": required,
                        "irrelevant_configured_rules": irrelevant,
                        "source_semantics_verified": False, "forecast_complete": False})
    expected = json.loads((root / "config/component-projection-contract-v1.json").read_text())["expected_enabled_leagues"]
    if len(leagues) != expected:
        raise ValueError("COMPONENT_ENABLED_LEAGUE_COUNT_DRIFT")
    return {"schema": "fie-component-portfolio-demand-v1", "research_only": True,
            "registry_sha256": digest(registry_path), "scoring_contract_sha256": digest(contracts_path),
            "enabled_leagues": len(leagues), "distinct_nonzero_configured_keys": len(configured),
            "distinct_relevant_keys": len({r["scoring_key"] for r in rows}),
            "required_components": sorted(components.values(), key=lambda r: r["component"]),
            "leagues": leagues, "rules": rows, "all_rule_mappings_registered": True,
            "source_semantics_verified": False, "complete_forecast_available": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    demand = build(a.root)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(demand, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: demand[k] for k in ("enabled_leagues", "distinct_nonzero_configured_keys", "distinct_relevant_keys", "complete_forecast_available")}))


if __name__ == "__main__":
    main()
