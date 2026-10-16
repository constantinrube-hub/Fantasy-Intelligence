"""Diagnostics must reconcile, preserve unknowns and never enter inference."""
import copy
import gzip
import itertools
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from component_weekly_ops import PROJECT, REFERENCE, digest, write_new, read
from component_diagnostics import parameter_rows, compare_snapshots, product_attribution, decompose_component, review, records, lines, snapshot
from component_challenger import validate_contract, validate_folds, CONTRACT
from component_refit_v3 import normalize_opponent

class AlgebraTests(unittest.TestCase):
    def test_symmetric_product_reconciles_every_factor_order(self):
        fp, ap = [40., .2, .75, 12.], [30., .1, .5, 10.]
        base = product_attribution(fp, ap, ['team', 'share', 'catch', 'yards'])
        self.assertAlmostEqual(sum(base.values()), 72 - 15)
        for order in itertools.permutations(range(4)):
            result = product_attribution([fp[i] for i in order], [ap[i] for i in order], [['team', 'share', 'catch', 'yards'][i] for i in order])
            for key in base:
                self.assertAlmostEqual(result[key], base[key])

    def test_only_volume_changes_efficiency_not_blamed(self):
        result = decompose_component({'targets': 8., 'receptions': 6., 'receiving_yards': 72.},
                                     {'targets': 4., 'receptions': 3., 'receiving_yards': 36.}, 'receiving_yards', ['targets', 'receptions', 'receiving_yards'])
        self.assertEqual(result['error'], 36)
        self.assertAlmostEqual(result['contributions']['player_opportunities'], 36)
        self.assertAlmostEqual(sum(v for k, v in result['contributions'].items() if k != 'player_opportunities'), 0)

    def test_team_volume_and_share_separated(self):
        result = decompose_component({'rushing_attempts': 10., 'rushing_yards': 50.}, {'rushing_attempts': 5., 'rushing_yards': 25.},
                                     'rushing_yards', ['rushing_attempts', 'rushing_yards'], (20., 20.))
        self.assertAlmostEqual(result['contributions']['team_opportunities'], 0)
        self.assertAlmostEqual(result['contributions']['player_share'], 25)

    def test_zero_parent_is_unidentifiable_not_zero_efficiency(self):
        result = decompose_component({'targets': 8., 'receptions': 6., 'receiving_yards': 72.},
                                     {'targets': 0., 'receptions': 0., 'receiving_yards': 0.}, 'receiving_yards', ['targets', 'receptions', 'receiving_yards'])
        self.assertEqual(result['status'], 'ZERO_PARENT_UNIDENTIFIABLE')
        self.assertEqual(result['error'], 72)
        self.assertFalse(result['contributions'])

    def test_unknown_factors_never_zero_imputed(self):
        result = decompose_component({'rushing_attempts': 5., 'rushing_yards': 20.}, {'rushing_yards': 0.}, 'rushing_yards', ['rushing_attempts', 'rushing_yards'])
        self.assertEqual(result['status'], 'MISSING_FACTOR_VALUES')

    def test_negative_yard_efficiency_allowed(self):
        result = decompose_component({'rushing_attempts': 2., 'rushing_yards': -2.}, {'rushing_attempts': 1., 'rushing_yards': -3.}, 'rushing_yards', ['rushing_attempts', 'rushing_yards'])
        self.assertEqual(result['status'], 'DECOMPOSED')
        self.assertAlmostEqual(sum(result['contributions'].values()), 1.)

class ParameterTests(unittest.TestCase):
    def value(self, version='V2', week=5, value=0., team='SEA'):
        return {'method_version': version, 'through_week': week, 'config_sha256': 'fixed',
                'parameters': [{'key': ['x'], 'value': value}], 'contexts': {'p': {'team': team}}}

    def test_zero_previous_relative_change_not_invented(self):
        result = compare_snapshots(self.value(value=2), self.value(value=0))
        self.assertEqual(result['changes'][0]['delta'], 2)
        self.assertIsNone(result['changes'][0]['relative_change'])

    def test_method_change_not_treated_as_parameter_drift(self):
        result = compare_snapshots(self.value('V3'), self.value('V2'))
        self.assertEqual(result['status'], 'METHOD_CHANGED_NOT_COMPARABLE')
        self.assertFalse(result['changes'])

    def test_future_snapshot_rejected(self):
        with self.assertRaisesRegex(ValueError, 'FUTURE'):
            compare_snapshots(self.value(week=5), self.value(week=6))

    def test_team_change_separate_from_numeric_change(self):
        result = compare_snapshots(self.value(team='DEN'), self.value(team='SEA'))
        self.assertEqual(result['changes'][0]['delta'], 0)
        self.assertEqual(result['context_changes'][0]['field'], 'team')

    def test_prior_only_defense_is_flagged(self):
        fit = {'rushing_defense': {'SEA': {'RB': {'allowed_ypc': 4., 'observed': {'carries': 0}}}}}
        row = next(r for r in parameter_rows(fit) if r['key'][0] == 'rushing_defense')
        self.assertEqual(row['support_status'], 'PRIOR_ONLY')

    def test_real_baseline_support_gap_is_visible(self):
        fit = read(PROJECT / REFERENCE / 'fit/source-refit-final.json')
        cells = {tuple(r['key'][:3]) for r in parameter_rows(fit) if r['support_status'] == 'PRIOR_ONLY'}
        self.assertEqual(len(cells), 256)

class ReviewTests(unittest.TestCase):
    def setup_data(self, root, actual_week=6):
        entities = [{'canonical_player_id': cid, 'team': 'SEA', 'position_model': 'WR', 'name': cid, 'fantasy_positions': ['WR']} for cid in ['p', 'q']]
        write_new(root / REFERENCE / 'verified/source-refit/entities.json', {'entities': entities})
        frozen = root / 'freeze'; frozen.mkdir()
        predictions = []
        for cid, target, rec, yards, probability in [('p', 8., 6., 72., .2), ('q', 2., 1., 12., .1)]:
            predictions.append({'model_id': 'A', 'canonical_player_id': cid, 'position_model': 'WR', 'season': 2026, 'week': 6,
                                'components': {'targets': target, 'receptions': rec, 'receiving_yards': yards, 'prob_rec_yd_100': probability},
                                'scores': {'L': {'mean': yards * .1}}, 'replay_only': False})
        lines(frozen / 'forecasts.jsonl.gz', predictions)
        write_new(frozen / 'profiles.json', [{'league_id': 'L', 'scoring_settings': {'rec_yd': .1}}])
        write_new(frozen / 'freeze-receipt.json', {'target_weeks': [6, 7, 8], 'sources': [],
                  'artifacts': {p.relative_to(root).as_posix(): digest(p) for p in frozen.iterdir()}})
        actual = root / 'actual'; actual.mkdir()
        outcomes = [{'canonical_player_id': cid, 'team': 'SEA', 'position_model': 'WR', 'season': 2026, 'week': actual_week,
                     'components': {'targets': target, 'receptions': rec, 'receiving_yards': yards, 'prob_rec_yd_100': probability}, 'basis': {}}
                    for cid, target, rec, yards, probability in [('p', 4., 3., 36., 1.), ('q', 6., 3., 30., 0.)]]
        lines(actual / 'actual-components.jsonl.gz', outcomes)
        write_new(actual / 'actual-receipt.json', {'artifacts': {p.relative_to(root).as_posix(): digest(p) for p in actual.iterdir()}})
        dest = root / 'config/contracts'; dest.mkdir(parents=True)
        shutil.copy2(PROJECT / 'config/contracts/runtime-contracts.json', dest / 'runtime-contracts.json')
        (root / 'research').mkdir()
        for name in ['component_scoring.py', 'component_registry.py']:
            shutil.copy2(PROJECT / 'research' / name, root / 'research' / name)

    def test_realistic_review_reconciles_and_uses_frozen_ranks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.setup_data(root)
            result = review(root, Path('freeze'), [Path('actual')], Path('review'))
            self.assertEqual(result['matched_values'], 8)
            rows = list(records(root / 'review/component-decomposition.jsonl.gz'))
            r = next(r for r in rows if r['canonical_player_id'] == 'p' and r['component'] == 'receiving_yards')
            self.assertEqual(r['pregame_component_rank'], 1)
            self.assertAlmostEqual(sum(r['contributions'].values()), 36.)
            self.assertEqual(r['lead_week'], 1)
            p = next(records(root / 'review/probability-metrics.jsonl.gz'))
            self.assertAlmostEqual(p['brier'], .325)
            impact = list(records(root / 'review/league-component-impact.jsonl.gz'))
            self.assertAlmostEqual(sum(r['fantasy_error_contribution'] for r in impact), 1.8)
            self.assertTrue(all(not r['independent_football_observation'] for r in impact))

    def test_week5_cannot_create_week6_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.setup_data(root, 5)
            result = review(root, Path('freeze'), [Path('actual')], Path('review'))
            self.assertEqual(result['status'], 'WAITING_FOR_OUTCOMES')
            self.assertEqual(result['matched_values'], 0)
            self.assertFalse(list(records(root / 'review/raw-errors.jsonl.gz')))

    def test_forecast_hash_drift_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.setup_data(root)
            (root / 'freeze/forecasts.jsonl.gz').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'DRIFT'):
                review(root, Path('freeze'), [], Path('review'))

class ChallengerTests(unittest.TestCase):
    def test_training_cannot_be_enabled_by_config_only(self):
        contract = read(CONTRACT); contract['training_enabled'] = True
        with self.assertRaisesRegex(ValueError, 'CHECKPOINT'):
            validate_contract(contract)

    def test_promotion_cannot_be_enabled(self):
        contract = read(CONTRACT); contract['automatic_promotion'] = True
        with self.assertRaisesRegex(ValueError, 'REPLACEMENT'):
            validate_contract(contract)

    def test_chronological_fold_enforced(self):
        self.assertTrue(validate_folds([{'train_end': 2022, 'validation_start': 2023, 'validation_end': 2023, 'test_start': 2024}]))
        with self.assertRaisesRegex(ValueError, 'CHRONOLOGICAL'):
            validate_folds([{'train_end': 2023, 'validation_start': 2022, 'validation_end': 2023, 'test_start': 2024}])

    def test_opponent_column_repair_is_explicit(self):
        import pandas as pd
        frame = pd.DataFrame({'opponent_team': ['SEA', 'DEN']})
        result = normalize_opponent(frame)
        self.assertEqual(result.opponent.tolist(), ['SEA', 'DEN'])
        self.assertNotIn('opponent', frame)

    def test_conflicting_opponent_columns_rejected(self):
        import pandas as pd
        with self.assertRaisesRegex(ValueError, 'CONFLICTING'):
            normalize_opponent(pd.DataFrame({'opponent': ['SEA'], 'opponent_team': ['DEN']}))

if __name__ == '__main__':
    unittest.main()
