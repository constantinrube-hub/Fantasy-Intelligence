"""Storage switches of run_week6_research_preparation.py (2026-11-15).

Checks, with every collaborator stubbed (no network, no repository data):
  1. switches off: the same files are written as before and the cycle report has no new keys;
  2. FIE_PREP_SKIP_EXPANDED=1: the waiver-expanded branch never runs, the research view gets no expanded inputs;
  3. FIE_PREP_SKIP_HEAVY_PRODUCTS=1: scenario_inputs, football_context and seven_report_products are not produced,
     league_evidence and the specialist freeze still are, and cycle.json carries digests instead of inline copies;
  4. in every case the raw source capture (weekly-sources) and the waiver-v2 forecast still run.
"""
from __future__ import annotations
import importlib, json, os, sys, tempfile, types
from pathlib import Path

HERE = Path(__file__).resolve().parent
CALLS: list[str] = []
BIG = {'rows': list(range(5000))}


def _mod(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m


def _write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def _stub(root: Path):
    def call(name, value=None):
        def f(*a, **k):
            CALLS.append(name)
            return value
        return f

    def capture(r, season, week):
        CALLS.append('raw_sources')
        env = r / 'data/research/prospective/weekly-sources/2026/week_11/T/source-envelope.json'
        _write(env, {'ok': True}); return env

    def expanded_prepare(r, envelope, output, completed_week=None):
        CALLS.append('expanded_prepare'); _write(Path(output) / 'live-history.json', BIG); return Path(output) / 'live-history.json'

    def research_view(r, envelope, canonical, ledger, expanded_capture, expanded_readiness):
        CALLS.append(f'research_view:{expanded_capture is not None}:{expanded_readiness is not None}'); return {'view': True}

    _mod('prospective_research_io', binding=lambda *a, **k: {'bound': True},
         clock=lambda s: __import__('datetime').datetime(2026, 11, 15, 12, 0, 0),
         encoded=lambda v: (json.dumps(v, sort_keys=True, indent=2) + '\n').encode(),
         gates=lambda blockers: {'activation_eligible': False, 'blockers': blockers},
         now=lambda: '2026-11-15T12:00:00Z', replay_response=lambda *a: b'', write=_write)
    _mod('capture_week6_research_sources', capture=capture, resolve_target=lambda s: 11,
         validate_manifest=lambda r, e: {'week': 11, 'season': 2026, 'captured_at': 'x', 'league_ids': ['1'],
                                         'responses': [{'name': 'schedule'}]})
    _mod('prepare_live_waiver_history', prepare=call('waiver_v2_history', Path('h.json')))
    _mod('capture_prospective_waiver', publish=call('waiver_v2_forecast', {'f': 1}))
    _mod('evaluate_prospective_waiver', evaluate=call('evaluate'))
    _mod('waiver_v2_prospective', ROOT=root)
    _mod('prepare_weekly_research_context', build=call('football_context', BIG))
    _mod('prepare_league_research_evidence', build=call('league_evidence', {'le': 1}))
    _mod('prepare_weekly_report_products', preparation=call('seven_report_products', BIG), markdown=lambda v: '# md\n')
    _mod('capture_retrospective_auction_history', capture=call('auction_history', {'a': 1}))
    _mod('scenario_readiness', build=call('scenario_readiness', {'s': 1}))
    _mod('prepare_weekly_scenario_inputs', build=call('scenario_inputs', BIG))
    _mod('freeze_specialist_strategy_choices', freeze=call('specialist_freeze', {'sp': 1}))
    _mod('window2d_context_foundation', parse_schedule_csv=lambda raw, s: [{'week': 11, 'kickoff': '2026-11-20T01:15:00Z'}])
    _mod('waiver_v2_expanded_runtime', prepare=expanded_prepare, publish=call('expanded_publish', {'e': 1}),
         load_lock=lambda r: ({'units': [], 'frozen_at': 'x'}, Path('lock.json')))
    _mod('prepare_research_readiness_ledger', build=call('readiness_ledger', {'l': 1}))
    _mod('publish_weekly_research_view', publish=research_view)
    _mod('prepare_weekly_model_outcomes', build=call('weekly_model_outcomes', {'o': 1}))


def _run(env: dict):
    CALLS.clear()
    for k in ('FIE_PREP_SKIP_EXPANDED', 'FIE_PREP_SKIP_HEAVY_PRODUCTS'):
        os.environ.pop(k, None)
    os.environ.update(env)
    root = Path(tempfile.mkdtemp())
    (root / 'config').mkdir(); (root / 'config/waiver-v2-expanded-scope.json').write_text('{}')
    _stub(root)
    sys.path.insert(0, str(HERE))
    sys.modules.pop('run_week6_research_preparation', None)
    mod = importlib.import_module('run_week6_research_preparation')
    report = mod.run(root, 2026, mode='capture')
    base = next((root / 'data/research/prospective/weekly-preparation/2026/week_11').iterdir())
    files = sorted(p.name for p in base.iterdir())
    cycle = json.loads((base / 'cycle.json').read_text())
    expanded = root / 'data/research/prospective/waiver-expanded'
    return report, files, cycle, list(CALLS), expanded.exists(), (base / 'cycle.json').stat().st_size


def test():
    off, files, cycle, calls, exp, size_off = _run({})
    assert files == ['cycle.json', 'expanded-readiness.json', 'football_context.json', 'league_evidence.json', 'readiness_ledger.json',
                     'scenario_inputs.json', 'scenario_readiness.json', 'seven_report_products.json', 'seven_report_products.md'], files
    assert set(cycle['operational_readiness']['counts']) == {'produced_stages', 'blocked_stages'}
    assert 'storage_policy' not in cycle and exp and 'expanded_prepare' in calls
    assert 'research_view:True:True' in calls

    rep, files, cycle, calls, exp, _ = _run({'FIE_PREP_SKIP_EXPANDED': '1'})
    assert not exp and 'expanded_prepare' not in calls and 'expanded_publish' not in calls
    assert 'research_view:False:False' in calls and 'expanded-readiness.json' not in files
    assert cycle['operational_readiness']['counts']['skipped_stages'] == 1 and cycle['storage_policy']['skip_expanded']
    assert rep['operational_readiness']['status'] == 'PARTIAL'

    rep, files, cycle, calls, exp, size_on = _run({'FIE_PREP_SKIP_EXPANDED': '1', 'FIE_PREP_SKIP_HEAVY_PRODUCTS': '1'})
    for name in ('scenario_inputs.json', 'football_context.json', 'seven_report_products.json', 'seven_report_products.md'):
        assert name not in files, name
    for name in ('league_evidence.json', 'scenario_readiness.json', 'readiness_ledger.json', 'cycle.json'):
        assert name in files, name
    assert 'specialist_freeze' in calls and not any(c in calls for c in ('football_context', 'scenario_inputs', 'seven_report_products'))
    assert all(s.get('result', {}).get('inline_omitted') for s in cycle['stages'] if isinstance(s.get('result'), dict))
    assert cycle['operational_readiness']['counts']['skipped_stages'] == 4
    assert size_on < size_off / 10, (size_on, size_off)

    for env in ({}, {'FIE_PREP_SKIP_EXPANDED': '1', 'FIE_PREP_SKIP_HEAVY_PRODUCTS': '1'}):
        _, _, _, calls, _, _ = _run(env)
        assert calls[0] == 'raw_sources' and 'waiver_v2_forecast' in calls and 'auction_history' in calls, calls
    print('integrity_prep_storage_policy_test: 4 cases OK')


if __name__ == '__main__':
    test()
