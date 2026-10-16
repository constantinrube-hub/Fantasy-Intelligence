#!/usr/bin/env python3
"""Static boundary for the additive Sunday M10/Sleeper checkpoint design."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "config/m10-sunday-paired-checkpoint-design.json"
DOC_PATH = ROOT / "docs/audits/M10_SUNDAY_PAIRED_CHECKPOINT_DESIGN.md"


def main() -> int:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    assert design["schema"] == "fie-m10-sleeper-sunday-checkpoint-design-v1"
    assert design["checkpoint_id"] == "SUNDAY_MAIN_T6"
    assert design["research_only"] is True and design["production_model"] == "M9"
    assert not any(design[key] for key in (
        "production_activation", "app_integration", "shadow_integration", "automatic_promotion"
    ))

    original = design["existing_week_open_capture"]
    assert original == {
        "identity": "WEEK_OPEN_FIRST_KICKOFF",
        "policy": "preserve_immutable",
        "replacement": False,
    }
    timing = design["timing"]
    assert timing["timezone"] == "America/New_York"
    assert timing["target_hours_before_anchor"] == timing["opens_hours_before_anchor"] == 6.0
    assert timing["closes_hours_before_anchor"] == 4.5 and timing["poll_minutes"] == 30
    assert timing["actual_observed_times_required"] is True

    # The local 07:00 target remains six real hours before 13:00 on both sides
    # of US DST; using the named zone avoids Berlin/US transition mismatches.
    eastern = ZoneInfo(timing["timezone"])
    for day in (datetime(2026, 10, 4, 13, tzinfo=eastern), datetime(2026, 11, 8, 13, tzinfo=eastern)):
        target = day - timedelta(hours=timing["target_hours_before_anchor"])
        assert target.hour == 7
        assert (day.astimezone(ZoneInfo("UTC")) - target.astimezone(ZoneInfo("UTC"))).total_seconds() == 21600

    cohort = design["eligible_cohort"]
    assert cohort["positions"] == ["QB", "RB", "WR", "TE"]
    assert cohort["minimum_lead_minutes"] == 30
    assert cohort["already_started_games"] == "excluded_symmetrically"
    assert "never impute" in cohort["missing_sleeper_policy"]
    assert set(cohort["coverage_reporting"]) == {
        "m10_eligible", "sleeper_rows", "identity_resolved", "matched", "excluded_by_reason"
    }

    safe = design["time_safety"]
    assert safe["target_week_realised_stats_in_m10_features"] is False
    assert safe["prior_completed_weeks_only"] is True
    assert safe["candidate_or_hyperparameter_change"] is False
    assert "excluded" in safe["current_week_earlier_game_outcomes"]

    coordinated = design["coordinated_capture"]
    assert coordinated["one_orchestrator"] and coordinated["shared_schedule_snapshot"]
    assert coordinated["maximum_source_drift_minutes"] == 10
    assert coordinated["source_timestamps_preserved"] is True
    assert coordinated["order"][0] == "schedule_and_checkpoint_decision"
    assert coordinated["order"][-1] == "pairing_manifest"

    namespaces = design["namespaces"]
    assert all("sunday-main-t6" in path for path in namespaces.values())
    assert all("checkpoints" in namespaces[key] for key in ("m10", "sleeper"))
    primary_contract = json.loads((ROOT / "config/m10-prospective-evidence-contract.json").read_text(encoding="utf-8"))
    assert primary_contract["weekly_freeze"]["primary_cutoff"].startswith("single immutable capture")
    assert namespaces["m10"] != primary_contract["namespaces"]["forecast"]

    comparison = design["comparison"]
    assert comparison["sleeper_raw_stats_scored_with_captured_league_profiles"] is True
    assert comparison["same_scorer_and_profile_hashes_as_m10"] is True
    assert comparison["promotion_effect"] == "none"
    assert comparison["decision_domains"].startswith("existing decision_validation_contract")

    storage = design["storage"]
    assert storage["first_write_immutable_per_checkpoint"] and storage["overwrite"] is False
    assert storage["historical_reconstruction"] is False
    assert {"NO_MAIN_SLATE", "WINDOW_MISSED", "SOURCE_DRIFT_EXCEEDED"} <= set(storage["missed_reasons"])

    forbidden = set(design["forbidden"])
    assert "overwrite week-open evidence" in forbidden
    assert "use target-week outcomes as M10 features" in forbidden
    assert "select the better checkpoint after outcomes" in forbidden
    assert "historical endpoint reconstruction" in forbidden

    doc = DOC_PATH.read_text(encoding="utf-8")
    for marker in (
        "SUNDAY_MAIN_T6", "WEEK_OPEN_FIRST_KICKOFF", "07:00 New York", "T-4.5",
        "realized statistics remain excluded", "maximum permitted gap", "ten",
        "imputed;", "M9 remains the production model"
    ):
        assert marker in doc, marker

    # This commit is design-only. The operational workflows still contain no
    # Sunday checkpoint identity; implementation follows after this boundary.
    for workflow in ("capture-fie-m10-prospective.yml", "capture-fie-market.yml"):
        assert "SUNDAY_MAIN_T6" not in (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")

    print("PASS Sunday paired-checkpoint design: additive T-6 identity, time-safe cohort and M9 governance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
