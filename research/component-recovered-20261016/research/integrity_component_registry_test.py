"""Scoring-demand guards and independently calculated expected-score examples."""
import json
from pathlib import Path
import unittest

from component_registry import ROOT, build, mapping, score_expected


class ComponentRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = json.loads((ROOT / "config/contracts/runtime-contracts.json").read_text())

    def test_entire_current_portfolio_registered_without_forecast_claim(self):
        d = build()
        registry = json.loads((ROOT / "data/research/leagues/registry.json").read_text())["leagues"]
        self.assertEqual({x["league_id"] for x in d["leagues"]}, {k for k,v in registry.items() if v.get("enabled") is True})
        self.assertEqual(d["enabled_leagues"], 23)
        self.assertFalse(d["complete_forecast_available"])
        self.assertFalse(d["source_semantics_verified"])
        self.assertTrue(all(not r["source_verified"] for r in d["rules"]))

    def test_unknown_rule_cannot_vanish(self):
        with self.assertRaisesRegex(ValueError, "UNKNOWN_SCORING_RULE"):
            mapping("unregistered_future_bonus", self.contracts)

    def test_trick_passes_and_specialist_fumbles_are_in_scope(self):
        r = score_expected({'pass_yd':.04,'pass_td':4,'fum_lost':-2},'RB',
                           {'passing_yards':20,'passing_touchdowns':1,'fumbles_lost':1},{},self.contracts)
        self.assertAlmostEqual(r['points'],2.8)
        self.assertIn('K',mapping('fum',self.contracts)['positions'])
        self.assertEqual(mapping('bonus_rec_te',self.contracts)['positions'],['TE'])

    def test_negative_receptions_and_signed_yards(self):
        r = score_expected({"rec": -.5,"rec_yd": .1},"WR",{"receptions":6,"receiving_yards":-2},{},self.contracts)
        self.assertAlmostEqual(r["points"], -3.2)

    def test_exclusive_game_bands_use_separate_probabilities(self):
        r = score_expected({"pass_yd":.04,"bonus_pass_yd_300":2,"bonus_pass_yd_400":1},"QB",
                           {"passing_yards":290},{"prob_pass_yd_300":.4,"prob_pass_yd_400":.1},self.contracts)
        self.assertAlmostEqual(r["points"], 12.5)

    def test_game_bonus_bands_do_not_stack_at_400_or_200(self):
        for key, lower, upper in [("bonus_pass_yd_300",300,399),("bonus_pass_yd_400",400,None),
                                 ("bonus_rush_yd_100",100,199),("bonus_rec_yd_100",100,199)]:
            b = mapping(key, self.contracts)["event_bounds"]
            self.assertEqual((b["lower_inclusive"], b["upper_inclusive"]), (lower,upper))

    def test_te_premium_and_missing_does_not_mean_zero(self):
        r = score_expected({"rec":1,"bonus_rec_te":.5},"TE",{"receptions":4},{},self.contracts)
        self.assertEqual(r["points"],6)
        r = score_expected({"rec":1,"fum_lost":-2},"WR",{"receptions":4},{},self.contracts)
        self.assertIsNone(r["points"])
        self.assertEqual(r["supported_subtotal"],4)

    def test_return_player_and_dst_are_separate(self):
        r = score_expected({"kr_yd":.1,"def_kr_yd":.1},"WR",{"kick_return_yards":30},{},self.contracts)
        self.assertEqual(r["points"],3)
        r = score_expected({"kr_yd":.1,"def_kr_yd":.1},"DEF",{"dst_kick_return_yards":50},{},self.contracts)
        self.assertEqual(r["points"],5)

    def test_idp_and_kicker_distance_aggregation(self):
        r = score_expected({"idp_tkl_solo":2,"idp_sack":4},"DL",{"idp_tackles_solo":3,"idp_sacks":.5},{},self.contracts)
        self.assertEqual(r["points"],8)
        r = score_expected({"fgm_50p":5},"K",{"kicker_fgm_50_59":.6,"kicker_fgm_60p":.1},{},self.contracts)
        self.assertAlmostEqual(r["points"],3.5)

    def test_invalid_probability_and_count_rejected(self):
        with self.assertRaisesRegex(ValueError,"PROBABILITY_OUT_OF_RANGE"):
            score_expected({"bonus_pass_yd_300":2},"QB",{},{"prob_pass_yd_300":1.1},self.contracts)
        with self.assertRaisesRegex(ValueError,"NEGATIVE_COUNT"):
            score_expected({"rec":1},"WR",{"receptions":-1},{},self.contracts)

    def test_exclusive_probability_sum_and_kicker_overlap_cannot_disagree(self):
        with self.assertRaisesRegex(ValueError,'EXCLUSIVE_PROBABILITY_SUM'):
            score_expected({'bonus_pass_yd_300':2},'QB',{},
                           {'prob_pass_yd_300':.8,'prob_pass_yd_400':.4},self.contracts)
        with self.assertRaisesRegex(ValueError,'DISTANCE_AGGREGATE_DISAGREEMENT'):
            score_expected({'fgm_50p':5},'K',{'kicker_fgm_50p':1,'kicker_fgm_50_59':.5,'kicker_fgm_60p':.2},
                           {},self.contracts)


if __name__ == "__main__":
    unittest.main()
