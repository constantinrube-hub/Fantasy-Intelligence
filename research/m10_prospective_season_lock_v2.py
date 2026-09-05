"""Corrected, portable M10 2026 research season lock (R8A).

This v2 path is additive: v1 remains preserved validation evidence and cannot be
installed for operational collection.  V2 binds a shared feature contract,
deterministic provenance, and residual-vector samples generated only on declared
out-of-sample folds.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import mean_absolute_error

from m10_prospective_capture_contract import ROOT, MODELS, POSITIONS, canonical_bytes, sha256_bytes, sha256_file
from m10_prospective_features import FEATURES, validate_feature_names
from m10_prospective_season_lock import (
    COUNT_TARGETS, CONTINUOUS_TARGETS, HGB_SCHEMA, SEASONS, choose_hgb,
    export_hgb, export_ridge, hgb_predict, load_json, matrix, ridge_predict,
)

LOCK_SCHEMA = "fie-m10-prospective-season-lock-v2"
INPUT_SCHEMA = "fie-m10-prospective-training-input-v2"
QUANTILES = (0.1, 0.25, 0.5, 0.75, 0.9)
FEATURE_CONTRACT = ROOT / "config/m10-prospective-feature-contract.json"
TARGET_CONTRACT = ROOT / "config/m10-prospective-target-contract.json"
RUNNER_DESIGN = ROOT / "config/m10-prospective-operational-runner-design.json"
OFFLINE = ROOT / "config/m10-offline-experiment.json"
CODE_PATHS = (
    "research/m10_prospective_features.py",
    "research/build_m10_prospective_historical_input_v2.py",
    "research/m10_prospective_season_lock_v2.py",
    "research/m10_prospective_season_lock.py",
    "research/fie_research.py",
)


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_json(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _contracts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    feature, target, runner, offline = _json(FEATURE_CONTRACT), _json(TARGET_CONTRACT), _json(RUNNER_DESIGN), _json(OFFLINE)
    assert feature["schema"] == "fie-m10-prospective-feature-contract-v2"
    assert target["schema"] == "fie-m10-prospective-target-contract-v2"
    assert runner["r8a_corrected_lock"]["schema"] == LOCK_SCHEMA
    assert tuple(feature["features"]) == FEATURES
    assert set(target["count_targets"]) == COUNT_TARGETS and set(target["continuous_targets"]) == CONTINUOUS_TARGETS
    return feature, target, runner, offline


def code_manifest() -> dict[str, Any]:
    files = [{"path": value, "sha256": sha256_file(ROOT / value)} for value in CODE_PATHS]
    return {"files": files, "sha256": _hash_json(files)}


def row_identity_manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    identity = [{key: row[key] for key in ("row_key", "season", "week", "canonical_player_id", "position_model", "team")} for row in rows]
    return sorted(identity, key=lambda row: row["row_key"])


def assert_input(value: dict[str, Any]) -> None:
    assert value["schema"] == INPUT_SCHEMA and value["training_target_seasons"] == list(SEASONS)
    assert value["historical_reconstruction"] is False
    validate_feature_names(value["feature_names"])
    assert value["source_files"] and all(len(item["sha256"]) == 64 for item in value["source_files"])
    rows = value["rows"]
    assert rows and all(int(row["season"]) in SEASONS for row in rows)
    assert len({row["row_key"] for row in rows}) == len(rows)
    forbidden = ("adp", "market", "projection", "draft", "replacement", "rank", "post_cutoff", "opponent_id", "team_id")
    for row in rows:
        assert row["position_model"] in POSITIONS and row["canonical_player_id"] and row["team"] and int(row["week"]) > 0
        assert set(row["features"]) == set(FEATURES)
        assert set(row["targets"]) <= COUNT_TARGETS | CONTINUOUS_TARGETS
        assert not any(token in name.lower() for name in list(row["features"]) + list(row["targets"]) for token in forbidden)
        for name, observed in row["targets"].items():
            if observed is None:
                continue
            assert np.isfinite(float(observed))
            if name in COUNT_TARGETS:
                assert float(observed) >= 0.0


def _feature_values(row: dict[str, Any]) -> list[float]:
    return [float("nan") if row["features"][name] is None else float(row["features"][name]) for name in FEATURES]


def _fold_hgb_candidate(rows: list[dict[str, Any]], target: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    years = sorted({int(row["season"]) for row in rows})
    if len(years) < 2:
        return dict(candidates[0])
    inner = years[-1]
    earlier = [row for row in rows if int(row["season"]) < inner]
    held = [row for row in rows if int(row["season"]) == inner]
    if len(earlier) < 40 or len(held) < 8:
        return dict(candidates[0])
    # Choose only from an inner split within the outer training window.  The
    # first fold has too little inner history and therefore uses its first
    # predeclared candidate rather than touching the outer test season.
    try:
        tx, ty = matrix(earlier, list(FEATURES), target)
        vx, vy = matrix(held, list(FEATURES), target, minimum=8)
        scored = []
        for index, candidate in enumerate(candidates):
            spec = export_hgb(tx, ty, list(FEATURES), target, candidate)
            scored.append((float(mean_absolute_error(vy, [hgb_predict(spec, row) for row in vx])), index, candidate))
        return dict(min(scored, key=lambda row: (row[0], row[1]))[2])
    except (AssertionError, ValueError):
        return dict(candidates[0])


def _constrain(vector: dict[str, float], *, prediction: bool = True) -> dict[str, float]:
    # Post-inference floors protect every model prediction. Observed continuous
    # yardage remains signed: a legitimate negative rushing/receiving/passing
    # result is an outcome, not an invalid count label.
    out = {name: max(0.0, float(value)) if prediction or name in COUNT_TARGETS else float(value) for name, value in vector.items()}
    if "completions" in out and "attempts" in out:
        out["completions"] = min(out["completions"], out["attempts"])
    if "receptions" in out and "targets" in out:
        out["receptions"] = min(out["receptions"], out["targets"])
    return out


def _reconcile(rows: list[dict[str, Any]], targets: list[str]) -> list[dict[str, Any]]:
    """Apply one shared generic team opportunity cap and structural constraints."""
    output = [dict(row) for row in rows]
    groups: dict[tuple[int, int, str], list[dict[str, Any]]] = {}
    for row in output:
        groups.setdefault((int(row["season"]), int(row["week"]), str(row["team"])), []).append(row)
    for group in groups.values():
        budgets = [row["features"].get("team_prior4_budget") for row in group]
        known = [float(value) for value in budgets if value is not None]
        budget = float(np.median(known)) if known else 0.0
        volumes = [name for name in ("targets", "carries") if name in targets]
        total = sum(float(row["prediction"].get(name, 0.0)) for row in group for name in volumes)
        if budget > 0.0 and total > budget:
            scale = budget / total
            for row in group:
                for name in volumes:
                    if name in row["prediction"]:
                        row["prediction"][name] *= scale
        for row in group:
            row["prediction"] = _constrain(row["prediction"])
    return output


def residual_samples(value: dict[str, Any], offline: dict[str, Any]) -> list[dict[str, Any]]:
    """Build canonical OOS residual vectors without using a fold's test outcomes in fitting."""
    samples: list[dict[str, Any]] = []
    for fold in offline["outer_folds"]:
        for position in POSITIONS:
            targets = list(offline["targets"][position])
            all_rows = [row for row in value["rows"] if row["position_model"] == position]
            train = [row for row in all_rows if int(row["season"]) in fold["train_seasons"]]
            test = [row for row in all_rows if int(row["season"]) == int(fold["test_season"]) and all(row["targets"].get(name) is not None for name in targets)]
            if not test:
                continue
            specs: dict[str, dict[str, Any]] = {model: {} for model in MODELS}
            for target in targets:
                x, y = matrix(train, list(FEATURES), target)
                hgb_candidate = _fold_hgb_candidate(train, target, offline["candidate_ladder"][2]["search_space"])
                specs["M9"][target] = export_ridge(x, y, list(FEATURES), 10.0, target)
                specs["M10_LINEAR"][target] = export_ridge(x, y, list(FEATURES), 6.0, target)
                specs["M10_HGB"][target] = export_hgb(x, y, list(FEATURES), target, hgb_candidate)
            for model in MODELS:
                predicted = []
                for row in test:
                    vector = {target: (ridge_predict if specs[model][target]["schema"] != HGB_SCHEMA else hgb_predict)(specs[model][target], _feature_values(row)) for target in targets}
                    predicted.append({**row, "prediction": vector})
                for row in _reconcile(predicted, targets):
                    actual = _constrain({name: float(row["targets"][name]) for name in targets}, prediction=False)
                    residual = {name: float(actual[name] - row["prediction"][name]) for name in targets}
                    samples.append({"position_model": position, "model": model, "test_season": int(fold["test_season"]), "row_key": row["row_key"], "residuals": residual})
    samples.sort(key=lambda row: (row["position_model"], row["model"], row["test_season"], row["row_key"]))
    assert samples and all(set(row["residuals"]) for row in samples)
    return samples


def make_fixture_input() -> dict[str, Any]:
    _, _, _, offline = _contracts()
    rows: list[dict[str, Any]] = []
    for season in SEASONS:
        for pos_index, position in enumerate(POSITIONS):
            for player in range(16):
                team = f"T{player % 4:02d}"
                base = float(5 + pos_index * 4 + player % 7 + season - 2019)
                targets = {name: round(max(0.0, base * (0.2 + index * 0.05)), 5) for index, name in enumerate(offline["targets"][position])}
                # Keep a legitimate negative continuous-yardage observation in
                # the first declared outer test season so the OOS residual
                # fixture proves that it is retained rather than zero-clamped.
                if player == 0 and season == 2022 and "rushing_yards" in targets:
                    targets["rushing_yards"] = -1.0
                row_key = f"{season}-01-fixture-{position.lower()}-{player}-{team}"
                rows.append({"row_key": row_key, "season": season, "week": 1, "canonical_player_id": f"fixture-{position.lower()}-{player}", "position_model": position, "team": team,
                             "features": {"player_prior4_volume": base, "player_prior4_efficiency": base / 3.0, "team_prior4_budget": base * 5.0}, "targets": targets})
    return {"schema": INPUT_SCHEMA, "training_target_seasons": list(SEASONS), "historical_reconstruction": False, "feature_names": list(FEATURES),
            "source_files": [{"path": "fixture/no-network-public-core-v2", "sha256": sha256_bytes(b"tranche7cr8-fixture-source-v1")}], "rows": rows}


def build_lock(value: dict[str, Any]) -> dict[str, Any]:
    assert_input(value)
    feature_contract, target_contract, runner, offline = _contracts()
    residuals = residual_samples(value, offline)
    code = code_manifest()
    identity = row_identity_manifest(value["rows"])
    # Final portable parameters are fitted only on 2019-2025. The implementation
    # deliberately reuses the already independently tested JSON exporters.
    models: dict[str, Any] = {}
    for position in POSITIONS:
        rows = [row for row in value["rows"] if row["position_model"] == position]
        models[position] = {}
        for target in offline["targets"][position]:
            x, y = matrix(rows, list(FEATURES), target)
            selected = choose_hgb(rows, list(FEATURES), target, offline["candidate_ladder"][2]["search_space"])
            variants = {"M9": export_ridge(x, y, list(FEATURES), 10.0, target), "M10_LINEAR": export_ridge(x, y, list(FEATURES), 6.0, target), "M10_HGB": export_hgb(x, y, list(FEATURES), target, selected)}
            probes = x[np.isfinite(x).all(axis=1)][:3]
            assert len(probes) == 3
            for spec in variants.values():
                predictor = hgb_predict if spec["schema"] == HGB_SCHEMA else ridge_predict
                spec["portable_probes"] = [{"features": [float(item) for item in row], "prediction": predictor(spec, [float(item) for item in row])} for row in probes]
                spec["parameter_sha256"] = _hash_json({key: val for key, val in spec.items() if key != "parameter_sha256"})
            models[position][target] = variants
    residual_manifest = [{key: row[key] for key in ("position_model", "model", "test_season", "row_key")} for row in residuals]
    lock = {
        "schema": LOCK_SCHEMA, "season": 2026, "first_write_immutable": True, "research_only": True, "production_model": "M9",
        "governance": {"production_activation": False, "app_integration": False, "runtime_integration": False, "shadow_integration": False, "automatic_promotion": False},
        "training_target_seasons": list(SEASONS), "forbidden_outcome_seasons": [2026], "feature_names": list(FEATURES), "source_files": value["source_files"],
        "training_matrix_sha256": _hash_json(value), "row_identity_manifest": identity, "row_identity_manifest_sha256": _hash_json(identity),
        "feature_contract_sha256": _hash_json(feature_contract), "target_contract_sha256": _hash_json(target_contract), "dependency_lock_sha256": sha256_file(ROOT / "research/requirements.txt"),
        "scorer_sha256": sha256_file(ROOT / "research/fie_research.py"), "training_code_manifest": code["files"], "training_code_manifest_sha256": code["sha256"],
        "candidate_config_sha256": _hash_json(offline), "rollout_design_sha256": _hash_json(runner), "residual_samples": residuals,
        "residual_samples_sha256": _hash_json(residuals), "residual_manifest": residual_manifest, "residual_manifest_sha256": _hash_json(residual_manifest),
        "residual_method": "out_of_sample_raw_component_residual_vectors_after_point_reconciliation_player_level_marginal_only", "models": models,
    }
    lock["season_lock_sha256"] = _hash_json(lock)
    return lock


def validate_lock(lock: dict[str, Any]) -> None:
    assert lock["schema"] == LOCK_SCHEMA and lock["season"] == 2026 and lock["training_target_seasons"] == list(SEASONS)
    assert lock["research_only"] and lock["production_model"] == "M9" and not any(lock["governance"].values())
    validate_feature_names(lock["feature_names"])
    copy = dict(lock); provided = copy.pop("season_lock_sha256"); assert provided == _hash_json(copy)
    assert lock["row_identity_manifest_sha256"] == _hash_json(lock["row_identity_manifest"])
    assert lock["residual_samples_sha256"] == _hash_json(lock["residual_samples"])
    assert lock["residual_manifest_sha256"] == _hash_json(lock["residual_manifest"])
    assert lock["training_code_manifest_sha256"] == _hash_json(lock["training_code_manifest"])
    feature, target, runner, _ = _contracts()
    assert lock["feature_contract_sha256"] == _hash_json(feature) and lock["target_contract_sha256"] == _hash_json(target) and lock["rollout_design_sha256"] == _hash_json(runner)
    assert lock["dependency_lock_sha256"] == sha256_file(ROOT / "research/requirements.txt") and lock["scorer_sha256"] == sha256_file(ROOT / "research/fie_research.py")
    assert lock["training_code_manifest"] == code_manifest()["files"]
    assert {(row["position_model"], row["model"]) for row in lock["residual_samples"]} == {(position, model) for position in POSITIONS for model in MODELS}
    for position, per_target in lock["models"].items():
        assert position in POSITIONS
        for variants in per_target.values():
            assert set(variants) == set(MODELS)
            for spec in variants.values():
                stored = spec["parameter_sha256"]
                assert stored == _hash_json({key: val for key, val in spec.items() if key != "parameter_sha256"})
                predictor = hgb_predict if spec["schema"] == HGB_SCHEMA else ridge_predict
                for probe in spec["portable_probes"]:
                    assert abs(predictor(spec, probe["features"]) - float(probe["prediction"])) <= 1e-10


def first_write(path: Path, lock: dict[str, Any]) -> str:
    payload = canonical_bytes(lock) + b"\n"
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("immutable corrected season lock already exists with different bytes")
        return "EXISTS"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return "CREATED"
