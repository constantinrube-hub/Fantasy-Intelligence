#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from window1d_optimal_waiver import (
    build_bid_ledger,
    build_bid_curve,
    candidate_signal,
    capture_history_for_league,
    empirical_win_probability,
    history_before_target,
    markdown_portfolio,
    normalize_waiver_transactions,
    plan_league,
    recommendation_from_curve,
    roster_manager_index,
    select_bid_sample,
    user_manager_index,
)


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def profile(fmt="REDRAFT"):
    return {
        "league_id": "123456789012345678",
        "league_name": "Fixture",
        "format": fmt,
        "profile_fingerprint": "fp",
        "total_rosters": 4,
        "roster_positions": ["QB", "RB", "WR", "TE", "FLEX", "BN", "BN"],
        "settings": {"playoff_week_start": 15, "waiver_budget": 100},
    }


def current(fmt="REDRAFT", generated=None, eligible=True):
    generated = generated or datetime.now(timezone.utc).isoformat()
    rows = [
        {"sleeper_id": "A", "full_name": "Add Alpha", "position_model": "RB", "team": "AAA", "waiver_activation_eligible": eligible, "waiver_next3_projection": 14.0 if eligible else None, "decision_weekly_projection": 12.0, "weekly_activation_eligible": True, "p10": 8.0, "waiver_feature_coverage": .8},
        {"sleeper_id": "B", "full_name": "Bench Beta", "position_model": "RB", "team": "BBB", "waiver_activation_eligible": True, "waiver_next3_projection": 8.0, "decision_weekly_projection": 7.0, "weekly_activation_eligible": True, "p10": 4.0},
        {"sleeper_id": "C", "full_name": "Starter C", "position_model": "RB", "team": "CCC", "waiver_activation_eligible": True, "waiver_next3_projection": 10.0, "decision_weekly_projection": 9.0, "weekly_activation_eligible": True, "p10": 5.0},
        {"sleeper_id": "Q", "full_name": "QB Q", "position_model": "QB", "team": "QQQ", "waiver_activation_eligible": True, "waiver_next3_projection": 18.0, "decision_weekly_projection": 17.0, "weekly_activation_eligible": True, "p10": 11.0},
    ]
    return {
        "league_id": "123456789012345678", "league_format": fmt, "profile_fingerprint": "fp",
        "profile_current_match": True, "season": 2026, "week": 2, "generated_at": generated,
        "target_week_realised_stats_excluded": True,
        "summary": {"waiver_activation_eligible": 4}, "players": rows,
    }


def live(fmt="REDRAFT"):
    return {"league_id": "123456789012345678", "name": "Fixture", "settings": {"waiver_budget": 100, "disable_adds": 0}, "total_rosters": 4}


def rosters():
    return [
        {"roster_id": 1, "owner_id": "u1", "players": ["B", "C", "Q", "X", "Y", "Z", "W"], "starters": ["Q", "C", "X", "Y", "B"], "settings": {"waiver_budget_used": 20}},
        {"roster_id": 2, "owner_id": "u2", "players": ["O2"], "settings": {"waiver_budget_used": 10}},
        {"roster_id": 3, "owner_id": "u3", "players": ["O3"], "settings": {"waiver_budget_used": 30}},
        {"roster_id": 4, "owner_id": "u4", "players": ["O4"], "settings": {"waiver_budget_used": 50}},
    ]


def users():
    return [
        {"user_id": "u1", "display_name": "C0nstant1n"},
        {"user_id": "u2", "display_name": "Other"},
        {"user_id": "u3", "display_name": "Rival"},
    ]


def history(n=20, position="RB", fmt="REDRAFT"):
    out = []
    for i in range(n):
        out.append({
            "portfolio_league_id": "123456789012345678", "source_league_id": "old", "season": 2025,
            "week": (i % 14) + 1, "league_format": fmt, "player_id": f"P{i}", "position": position,
            "bid": float(5 + i), "budget_cap": 100.0, "bid_pct_cap": (5 + i) / 100.0,
            "is_winning_bid": True, "is_failed_claim": False, "is_explicit_competitive_loss": False,
        })
    return out


def run():
    # 1. Sleeper complete waiver becomes an observable winning bid.
    tx = [{"type": "waiver", "status": "complete", "transaction_id": "t1", "settings": {"waiver_bid": 17}, "adds": {"A": 1}}]
    obs = normalize_waiver_transactions(tx, portfolio_league_id="L", source_league_id="L", season=2026, week=1, league_format="REDRAFT", budget_cap=100)
    assert_true(len(obs) == 1 and obs[0]["is_winning_bid"] and obs[0]["bid"] == 17, "winning bid normalization")

    # 2. Failed claims are not automatically called competitive losses.
    tx2 = [{"type": "waiver", "status": "failed", "transaction_id": "t2", "settings": {"waiver_bid": 12}, "adds": {"A": 1}, "metadata": {"note": "roster full"}}]
    o2 = normalize_waiver_transactions(tx2, portfolio_league_id="L", source_league_id="L", season=2026, week=1, league_format="REDRAFT", budget_cap=100)[0]
    assert_true(o2["is_failed_claim"] and not o2["is_explicit_competitive_loss"], "failed claim conservative semantics")
    tx3 = [{"type": "waiver", "status": "failed", "transaction_id": "t3", "settings": {"waiver_bid": 12}, "adds": {"A": 1}, "metadata": {"note": "outbid by higher bid"}}]
    o3 = normalize_waiver_transactions(tx3, portfolio_league_id="L", source_league_id="L", season=2026, week=1, league_format="REDRAFT", budget_cap=100)[0]
    assert_true(o3["is_explicit_competitive_loss"], "explicit outbid metadata")

    # 3. Manager identity and the player-level bid ledger remain observation-only.
    managers = roster_manager_index(rosters(), users(), "C0nstant1n")
    assert_true(managers["1"]["is_managed_user"] and managers["1"]["manager_name"] == "C0nstant1n", "managed identity")
    ledger_tx = [
        {"type": "waiver", "status": "complete", "transaction_id": "w", "creator": "u2", "created": 3, "settings": {"waiver_bid": 41}, "adds": {"A": 2}},
        {"type": "waiver", "status": "failed", "transaction_id": "m", "creator": "u1", "created": 1, "settings": {"waiver_bid": 27}, "adds": {"A": 1}, "metadata": {"notes": "claimed by another owner"}},
        {"type": "waiver", "status": "failed", "transaction_id": "o", "creator": "u3", "created": 2, "settings": {"waiver_bid": 30}, "adds": {"A": 3}, "metadata": {"notes": "claimed by another owner"}},
    ]
    ledger_obs = normalize_waiver_transactions(
        ledger_tx, portfolio_league_id="L", source_league_id="L", season=2026,
        week=3, league_format="REDRAFT", budget_cap=100, managers_by_roster=managers,
        managers_by_user=user_manager_index(users(), "C0nstant1n"),
    )
    ledger = build_bid_ledger(ledger_obs)
    assert_true(len(ledger) == 1 and ledger[0]["winning_claim"]["manager_name"] == "Other", "winner manager")
    assert_true(ledger[0]["managed_user_highest_bid"] == 27 and len(ledger[0]["managed_user_claims"]) == 1, "managed bid")
    assert_true(len(ledger[0]["other_observed_failed_claims"]) == 1 and ledger[0]["visibility"] == "PARTIAL_OBSERVED", "other observed failures")
    assert_true("complete private bid book" in ledger[0]["visibility_note"], "visibility disclaimer")
    rendered = markdown_portfolio({
        "week": 3, "generated_at": "fixture", "leagues": [{
            "league_id": "L", "league_name": "Fixture", "format": "REDRAFT",
            "status": "BLOCKED_STALE_CURRENT",
            "observed_target_week_bid_ledger": {"players": ledger},
        }],
    })
    assert_true("41.0 · Other" in rendered and "27.0 (failed)" in rendered and "30.0 · Rival" in rendered, "ledger markdown")

    # 4. Historical capture resolves managers but still preserves missing bids as unknown.
    def history_fetcher(url):
        if url.endswith("/league/L"):
            return {"season": 2026, "settings": {"waiver_budget": 100}}
        if url.endswith("/league/L/rosters"):
            return rosters()
        if url.endswith("/league/L/users"):
            return users()
        if url.endswith("/league/L/transactions/1"):
            return ledger_tx
        raise AssertionError(url)
    captured = capture_history_for_league(
        "L", "REDRAFT", 2026, 1, username="C0nstant1n", max_seasons=1,
        fetcher=history_fetcher,
    )
    assert_true(captured["schema"].endswith("-v2") and captured["summary"]["player_week_ledgers"] == 1, "history v2 ledger")
    assert_true(captured["summary"]["manager_resolved_observations"] == 3, "history manager coverage")

    # 5. Target-week leakage is excluded.
    hs = history(4) + [{**history(1)[0], "season": 2026, "week": 2, "bid": 99, "bid_pct_cap": .99}]
    clean = history_before_target(hs, 2026, 2)
    assert_true(all(not (x["season"] == 2026 and x["week"] >= 2) for x in clean), "target week excluded")

    # 6. Hierarchical sample prefers league+position when enough evidence exists.
    sample = select_bid_sample(history(8), league_id="123456789012345678", league_format="REDRAFT", position="RB", season=2026, week=2)
    assert_true(sample["scope"] == "LEAGUE_POSITION" and sample["n"] == 8, "sample hierarchy")

    # 7. Empirical win probability rises with bid and uses smoothing.
    smp = history(10)
    p1 = empirical_win_probability(smp, .06)
    p2 = empirical_win_probability(smp, .20)
    assert_true(p1 is not None and p2 is not None and 0 < p1 < p2 < 1, "empirical probability monotonic")

    # 8. Bid curve never exceeds remaining budget and recommendation is on-curve.
    curve = build_bid_curve(sample=history(15), budget_cap=100, own_remaining=37, opponent_budgets=[90, 50, 20], player_utility_index=90, preservation_weight=.8)
    rec = recommendation_from_curve(curve)
    assert_true(curve[-1]["bid"] == 37 and rec is not None and 0 <= rec["recommended_bid"] <= 37, "budget bound")
    probs = [x["estimated_win_probability"] for x in curve]
    assert_true(all(b >= a for a, b in zip(probs, probs[1:])), "win curve monotonic")

    # 9. Standard league produces an empirical recommendation from governed waiver evidence.
    plan = plan_league(
        league_id="123456789012345678", profile=profile(), current=current(), live_league=live(),
        rosters=rosters(), users=users(), username="C0nstant1n", all_history=history(20),
        target_season=2026, target_week=2, now=datetime.now(timezone.utc),
    )
    assert_true(plan["engine"] == "STANDARD" and plan["recommendation_count"] >= 1, "standard plan")
    assert_true(all((x.get("recommendation") or {}).get("recommended_bid", 0) <= 80 for x in plan["recommendations"]), "own budget respected")

    # 10. Chopped uses a distinct engine and exposes future-supply context.
    chopped_plan = plan_league(
        league_id="123456789012345678", profile=profile("CHOPPED"), current=current("CHOPPED"), live_league=live("CHOPPED"),
        rosters=rosters(), users=users(), username="C0nstant1n", all_history=history(20, fmt="CHOPPED"),
        target_season=2026, target_week=2, now=datetime.now(timezone.utc),
    )
    assert_true(chopped_plan["engine"] == "CHOPPED" and chopped_plan["chopped_context"] is not None, "chopped specialization")

    # 11. Profile drift fails closed.
    c = current(); c["profile_current_match"] = False
    drift = plan_league(league_id="123456789012345678", profile=profile(), current=c, live_league=live(), rosters=rosters(), users=users(), username="C0nstant1n", all_history=history(), target_season=2026, target_week=2)
    assert_true(drift["status"] == "BLOCKED_PROFILE_DRIFT", "profile drift blocker")

    # 12. Stale current fails closed.
    stale_current = current(generated=(datetime.now(timezone.utc) - timedelta(hours=50)).isoformat())
    stale = plan_league(league_id="123456789012345678", profile=profile(), current=stale_current, live_league=live(), rosters=rosters(), users=users(), username="C0nstant1n", all_history=history(), target_season=2026, target_week=2, max_current_age_hours=36)
    assert_true(stale["status"] == "BLOCKED_STALE_CURRENT", "staleness blocker")

    # 13. Target-week realized-stat protection is mandatory.
    leak_current = current(); leak_current["target_week_realised_stats_excluded"] = False
    leak = plan_league(league_id="123456789012345678", profile=profile(), current=leak_current, live_league=live(), rosters=rosters(), users=users(), username="C0nstant1n", all_history=history(), target_season=2026, target_week=2)
    assert_true(leak["status"] == "BLOCKED_TARGET_WEEK_REALIZED_STATS_NOT_EXCLUDED", "realized stats blocker")

    # 14. No eligible waiver projection remains a typed blocker, never a zero-imputed plan.
    none = current(eligible=False)
    blocked = plan_league(league_id="123456789012345678", profile=profile(), current=none, live_league=live(), rosters=rosters(), users=users(), username="C0nstant1n", all_history=history(), target_season=2026, target_week=2)
    assert_true(blocked["status"] == "BLOCKED_NO_ELIGIBLE_WAIVER_PROJECTIONS", "no waiver evidence blocker")

    # 15. Missing drop evidence is not treated as zero.
    idx = {x["sleeper_id"]: x for x in current()["players"]}
    own = rosters()[0]
    idx["B"]["waiver_activation_eligible"] = False; idx["B"]["waiver_next3_projection"] = None
    idx["C"]["waiver_activation_eligible"] = False; idx["C"]["waiver_next3_projection"] = None
    idx["Q"]["waiver_activation_eligible"] = False; idx["Q"]["waiver_next3_projection"] = None
    sig = candidate_signal(current()["players"][0], own, profile(), idx, chopped=False)
    assert_true(sig is not None and sig["status"] == "BLOCKED_DROP_VALUE_UNAVAILABLE", "no zero-imputed drop")

    print("PASS Window 1D optimal waiver + Chopped integrity (15 checks)")


if __name__ == "__main__":
    run()
