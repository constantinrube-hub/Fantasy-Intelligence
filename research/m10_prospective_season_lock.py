#!/usr/bin/env python3
"""Immutable, portable 2026 research season lock (Tranche 7C-R1).

This builder only consumes an explicit, hashable historical matrix.  It never
contacts a provider, trains during inference, or touches application data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from m10_prospective_capture_contract import ROOT, MODELS, POSITIONS, canonical_bytes, sha256_bytes, write_json

LOCK_SCHEMA = "fie-m10-prospective-season-lock-v1"
INPUT_SCHEMA = "fie-m10-prospective-training-input-v1"
HGB_SCHEMA = "fie-hgb-tree-v1"
SEASONS = tuple(range(2019, 2026))
COUNT_TARGETS = {"attempts", "completions", "passing_tds", "interceptions", "carries", "rushing_tds", "targets", "receptions", "receiving_tds"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rollout() -> dict[str, Any]:
    value = load_json(ROOT / "config/m10-prospective-rollout-design.json")
    assert value["season_lock"]["season"] == 2026 and value["production_model"] == "M9"
    assert value["research_only"] and not any(value[key] for key in ("production_activation", "app_integration", "runtime_integration", "shadow_integration"))
    return value


def experiment() -> dict[str, Any]:
    return load_json(ROOT / "config/m10-offline-experiment.json")


def assert_input(value: dict[str, Any]) -> None:
    assert value["schema"] == INPUT_SCHEMA and value["training_target_seasons"] == list(SEASONS)
    assert value["historical_reconstruction"] is False
    assert value["feature_names"] and all(isinstance(x, str) for x in value["feature_names"])
    assert value["source_files"] and all(len(x["sha256"]) == 64 for x in value["source_files"])
    rows = value["rows"]
    assert rows and all(int(row["season"]) in SEASONS for row in rows)
    forbidden = ("adp", "market", "sleeper_projection", "draft", "replacement", "rank", "post_cutoff", "opponent_id", "team_id")
    for row in rows:
        assert row["position_model"] in POSITIONS and row["canonical_player_id"]
        assert set(row["features"]) == set(value["feature_names"])
        assert not any(token in key.lower() for key in list(row["features"]) + list(row["targets"]) for token in forbidden)


def matrix(rows: list[dict[str, Any]], features: list[str], target: str, minimum: int = 40) -> tuple[np.ndarray, np.ndarray]:
    selected = [row for row in rows if target in row["targets"] and row["targets"][target] is not None]
    assert len(selected) >= minimum, f"insufficient eligible rows for {target}"
    x = np.asarray([[row["features"][name] for name in features] for row in selected], dtype=float)
    y = np.asarray([row["targets"][target] for row in selected], dtype=float)
    assert np.isfinite(y).all() and (y >= 0).all()
    return x, y


def export_ridge(x: np.ndarray, y: np.ndarray, features: list[str], alpha: float, target: str) -> dict[str, Any]:
    model = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
    model.fit(x, y)
    imp, scale, ridge = model.named_steps["impute"], model.named_steps["scale"], model.named_steps["ridge"]
    return {"schema": "fie-ridge-linear-v1", "target": target, "features": features, "alpha": alpha,
            "imputer_medians": [float(v) for v in imp.statistics_], "scaler_mean": [float(v) for v in scale.mean_],
            "scaler_scale": [float(v) if float(v) else 1.0 for v in scale.scale_], "coefficients": [float(v) for v in ridge.coef_],
            "intercept": float(ridge.intercept_), "n_train": int(len(y)), "prediction_floor": 0.0}


def ridge_predict(spec: dict[str, Any], values: list[float]) -> float:
    z = np.asarray(values, dtype=float)
    med = np.asarray(spec["imputer_medians"], dtype=float)
    z = np.where(np.isfinite(z), z, med)
    value = float(np.dot((z - np.asarray(spec["scaler_mean"])) / np.asarray(spec["scaler_scale"]), np.asarray(spec["coefficients"])) + spec["intercept"])
    return max(float(spec["prediction_floor"]), value)


def loss_for(target: str, y: np.ndarray) -> str:
    return "poisson" if target in COUNT_TARGETS and float(y.sum()) > 0 else "squared_error"


def export_hgb(x: np.ndarray, y: np.ndarray, features: list[str], target: str, candidate: dict[str, Any]) -> dict[str, Any]:
    imp = SimpleImputer(strategy="median"); tx = imp.fit_transform(x)
    model = HistGradientBoostingRegressor(loss=loss_for(target, y), random_state=106, **candidate).fit(tx, y)
    iterations = []
    for predictors in model._predictors:
        tree = predictors[0]
        nodes = []
        for node in tree.nodes:
            nodes.append({"value": float(node["value"]), "feature_idx": int(node["feature_idx"]), "num_threshold": float(node["num_threshold"]),
                          "missing_go_to_left": bool(node["missing_go_to_left"]), "left": int(node["left"]), "right": int(node["right"]), "is_leaf": bool(node["is_leaf"])})
        iterations.append({"nodes": nodes})
    spec = {"schema": HGB_SCHEMA, "target": target, "features": features, "imputer_medians": [float(v) for v in imp.statistics_],
            "baseline_prediction": float(np.ravel(model._baseline_prediction)[0]), "iterations": iterations,
            "loss": loss_for(target, y), "learning_rate": float(candidate["learning_rate"]), "candidate": candidate, "n_train": int(len(y)), "prediction_floor": 0.0}
    spec["sklearn_export_probes"] = [{"features": [float(v) for v in row], "prediction": float(max(0.0, value))} for row, value in zip(x[:3], model.predict(imp.transform(x[:3])))]
    return spec


def hgb_predict(spec: dict[str, Any], values: list[float]) -> float:
    z = np.asarray(values, dtype=float); med = np.asarray(spec["imputer_medians"], dtype=float); z = np.where(np.isfinite(z), z, med)
    result = float(spec["baseline_prediction"])
    for item in spec["iterations"]:
        nodes, index = item["nodes"], 0
        while not nodes[index]["is_leaf"]:
            node, value = nodes[index], z[nodes[index]["feature_idx"]]
            index = node["left"] if (not np.isfinite(value) and node["missing_go_to_left"]) or (np.isfinite(value) and value <= node["num_threshold"]) else node["right"]
        result += nodes[index]["value"]
    return max(float(spec["prediction_floor"]), result)


def choose_hgb(rows: list[dict[str, Any]], features: list[str], target: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    old, late = [r for r in rows if r["season"] <= 2024], [r for r in rows if r["season"] == 2025]
    scored = []
    for candidate in candidates:
        x, y = matrix(old, features, target); spec = export_hgb(x, y, features, target, candidate)
        vx, vy = matrix(late, features, target, minimum=8); scored.append((float(mean_absolute_error(vy, [hgb_predict(spec, row) for row in vx])), candidate))
    return min(scored, key=lambda item: (item[0], canonical_bytes(item[1])))[1]


def make_fixture_input() -> dict[str, Any]:
    targets, rows, features = experiment()["targets"], [], ["player_prior4_volume", "player_prior4_efficiency", "team_prior4_budget"]
    for season in SEASONS:
        for position_index, position in enumerate(POSITIONS):
            for player in range(8):
                base = float(position_index * 3 + player + season - 2018)
                result = {name: round(max(0.0, base * (0.35 + index * .07)), 4) for index, name in enumerate(targets[position])}
                rows.append({"season": season, "position_model": position, "canonical_player_id": f"fixture-{position.lower()}-{player}",
                             "features": {features[0]: base, features[1]: base / 3.0, features[2]: base * 1.7}, "targets": result})
    return {"schema": INPUT_SCHEMA, "training_target_seasons": list(SEASONS), "historical_reconstruction": False, "feature_names": features,
            "source_files": [{"path": "fixture/no-network-public-core-matrix-v1", "sha256": sha256_bytes(b"tranche7cr-fixture-source-v1")}], "rows": rows}


def build_lock(value: dict[str, Any]) -> dict[str, Any]:
    assert_input(value); design, offline = rollout(), experiment(); features = value["feature_names"]
    models: dict[str, Any] = {}
    for position in POSITIONS:
        rows = [row for row in value["rows"] if row["position_model"] == position]
        per_target: dict[str, Any] = {}
        for target in offline["targets"][position]:
            x, y = matrix(rows, features, target); selected = choose_hgb(rows, features, target, offline["candidate_ladder"][2]["search_space"])
            entries = {"M9": export_ridge(x, y, features, 10.0, target), "M10_LINEAR": export_ridge(x, y, features, 6.0, target), "M10_HGB": export_hgb(x, y, features, target, selected)}
            for spec in entries.values():
                probes = [[float(v) for v in row] for row in x[:3]]
                predictor = ridge_predict if spec["schema"] != HGB_SCHEMA else hgb_predict
                spec["portable_probes"] = [{"features": row, "prediction": predictor(spec, row)} for row in probes]
                spec["parameter_sha256"] = sha256_bytes(canonical_bytes({k: v for k, v in spec.items() if k != "parameter_sha256"}))
            per_target[target] = entries
        models[position] = per_target
    training_sha = sha256_bytes(canonical_bytes(value))
    lock = {"schema": LOCK_SCHEMA, "season": 2026, "first_write_immutable": True, "research_only": True, "production_model": "M9",
            "governance": {"production_activation": False, "app_integration": False, "runtime_integration": False, "shadow_integration": False, "automatic_promotion": False},
            "training_target_seasons": list(SEASONS), "forbidden_outcome_seasons": [2026], "training_matrix_sha256": training_sha,
            "source_files": value["source_files"], "feature_names": features, "rollout_design_sha256": sha256_bytes(canonical_bytes(design)),
            "offline_candidate_config_sha256": sha256_bytes(canonical_bytes(offline)), "models": models}
    lock["season_lock_sha256"] = sha256_bytes(canonical_bytes(lock)); return lock


def validate_lock(lock: dict[str, Any]) -> None:
    assert lock["schema"] == LOCK_SCHEMA and lock["season"] == 2026 and lock["training_target_seasons"] == list(SEASONS)
    assert lock["research_only"] and lock["production_model"] == "M9" and not any(lock["governance"].values())
    copy = dict(lock); supplied = copy.pop("season_lock_sha256"); assert supplied == sha256_bytes(canonical_bytes(copy))
    for position, targets in lock["models"].items():
        assert position in POSITIONS
        for variants in targets.values():
            assert set(variants) == set(MODELS)
            for spec in variants.values():
                stored = spec.pop("parameter_sha256"); assert stored == sha256_bytes(canonical_bytes(spec)); spec["parameter_sha256"] = stored
                predictor = hgb_predict if spec["schema"] == HGB_SCHEMA else ridge_predict
                for probe in spec["portable_probes"]:
                    assert abs(predictor(spec, probe["features"]) - float(probe["prediction"])) <= 1e-10
                if spec["schema"] == HGB_SCHEMA:
                    for probe in spec["sklearn_export_probes"]:
                        assert abs(hgb_predict(spec, probe["features"]) - float(probe["prediction"])) <= 1e-10
                assert spec["prediction_floor"] == 0.0


def first_write(path: Path, lock: dict[str, Any]) -> str:
    payload = canonical_bytes(lock) + b"\n"
    if path.exists():
        if path.read_bytes() != payload: raise ValueError("immutable season lock already exists with different bytes")
        return "EXISTS"
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload); return "CREATED"
