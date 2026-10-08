#!/usr/bin/env python3
"""Product completeness, time, target, and immutable-owner preservation checks."""
import json
import tempfile
from pathlib import Path
import weekly_report_bundle as w


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        now = w.stamp('2026-10-08T01:00:00Z')
        empty = w.bundle(root, 2026, 5, now)
        assert len(empty['products']) == 7 and empty['complete_product_count'] == 0
        assert all(row['status'] == 'BLOCKED_MISSING_PRODUCT' for row in empty['products'].values())
        assert all(row['readiness']['blocking_reasons'] == ['OWNER_OUTPUT_MISSING_OR_INVALID'] for row in empty['products'].values())
        base = root / 'data/research/evaluation/2026/weeks/week-5'
        path = base / 'waivers/portfolio-latest.json'
        path.parent.mkdir(parents=True)
        rows = [{'league_id': 'a', 'season': 2026, 'week': 5, 'format': 'REDRAFT', 'status': 'BLOCKED'},
                {'league_id': 'z', 'season': 2026, 'week': 5, 'format': 'CHOPPED', 'status': 'PARTIAL'}]
        value = {'schema': 'fie-window1d-optimal-waiver-portfolio-v1', 'season': 2026, 'week': 5,
                 'as_of_utc': '2026-10-08T00:00:00Z', 'generated_at': '2026-10-08T00:30:00Z', 'leagues': rows}
        path.write_text(json.dumps(value))
        before = path.read_bytes()
        report = w.bundle(root, 2026, 5, now)
        waiver = report['products']['WAIVER_GUIDE']
        assert waiver['status'] == 'PARTIAL_OWNER_OUTPUT' and waiver['complete'] is False
        assert waiver['content']['leagues'][0]['league_id'] == 'z'
        assert waiver['readiness']['evidence']['league_count'] == 2
        assert 'OFFENSIVE_WAIVER_RECOMMENDATIONS_ABSENT' in waiver['readiness']['blocking_reasons']
        assert report['complete_product_count'] == 0 and path.read_bytes() == before
        assert report['products']['DST_HOLD_STREAM']['status'] == 'BLOCKED_MISSING_PRODUCT'
        for mutate, reason in [
            (lambda v: v.update(week=4), 'TARGET_MISMATCH'),
            (lambda v: v.update(generated_at='2026-10-08T02:00:00Z'), 'AFTER_AS_OF'),
            (lambda v: v.update(as_of_utc='2026-10-05T00:00:00Z'), 'STALE'),
            (lambda v: v.update(leagues=[rows[0], rows[0]]), 'DUPLICATE'),
            (lambda v: v.update(schema='unknown'), 'SCHEMA_MISMATCH'),
        ]:
            altered = json.loads(before)
            mutate(altered)
            path.write_text(json.dumps(altered))
            rejected = w.bundle(root, 2026, 5, now)
            source = rejected['sources']['WINDOW_1D']
            assert source['status'] == 'BLOCKED_INVALID_SOURCE' and reason in source['reason'], source
            assert rejected['products']['WAIVER_GUIDE']['content'] is None
        path.write_text(before.decode())
        from in_season_pr2_weekly_lineups import capture_payload, sha256_value
        pr2_path = base / 'lineups/portfolio-latest.json'
        pr2_path.parent.mkdir(parents=True)
        opponent = {'status':'CAPTURED_H2H_CONTEXT','opponent_roster_id':2, 'captured_at':'2026-10-08T00:20:00Z',
                    'opponent_submitted_starters':{'status':'CAPTURED_SUBMITTED_STARTER_IDS', 'player_id_namespace':'sleeper', 'player_ids':['123']},
                    'opponent_lineup':{'status':'EXACT_MAX_MEAN_ADVISORY','selected_player_ids':['gsis-x'],'actionable':False}}
        pr2 = {'schema':'fie-in-season-pr2-weekly-lineup-portfolio-v1', 'generated_at':'2026-10-08T00:30:00Z',
               'leagues':[{'league_id':'a','season':2026,'week':5,'format':'REDRAFT','opponent_context':opponent,
                           'evidence':{'scoring_signature':'sig','profile_fingerprint':'profile'}},
                          {'league_id':'z','season':2026,'week':5,'format':'CHOPPED','opponent_context':opponent}],
               'portfolio_intelligence':{'cross_league_exposure':[]}}
        content_hash = sha256_value(capture_payload(pr2))
        pr2.update(capture_id=content_hash[:16],capture_content_sha256=content_hash)
        frozen = pr2_path.parent / 'captures' / f'portfolio-{content_hash[:16]}.json'
        frozen.parent.mkdir();frozen.write_text(json.dumps(pr2));pr2_path.write_text(json.dumps(pr2))
        good = w.bundle(root,2026,5,now)
        assert good['sources']['PR2']['capture_sha256'] == w.digest(frozen)
        contexts = good['products']['EXPOSURE']['content']['captured_opponent_contexts']
        assert contexts[0]['owner_context'] == opponent and not contexts[0]['actionable']
        assert contexts[1]['kind']=='CHOPPED_FIELD' and contexts[1]['owner_context'] is None
        chopped_bestball = {**pr2['leagues'][1], 'format': 'CHOPPED_BESTBALL'}
        assert w.captured_opponent_contexts({**pr2, 'leagues': [chopped_bestball]})[0]['kind'] == 'CHOPPED_FIELD'
        assert 'Captured opponent context' in w.markdown(good)
        inputs = root / 'config' / 'frozen.json';inputs.parent.mkdir();inputs.write_text('{}')
        surface_path = root / 'data/operations/portfolio-surface.json';surface_path.parent.mkdir(parents=True)
        surface = {'schema':'fie-weekly-portfolio-surface-v1','season':2026,'week':5,
                   'as_of_utc':'2026-10-08T00:45:00Z','input_hashes':{'config/frozen.json':w.digest(inputs)},
                   'roster_exposure':[],'league_status_counts':{'BOUND_CURRENT_ROSTER':1},
                   'specialist_evidence':{},'leagues':[{'league_id':'a','status':'BOUND_CURRENT_ROSTER',
                       'active_operational_scope':True,'scoring_signature':'sig','profile_fingerprint':'profile',
                       'players':[{'sleeper_id':'123','player_id':'gsis-1','player_name':'One','team':'AAA',
                                   'position':'WR','owned_by_user':False,'rostered_in_league':True,
                                   'fie_mean':None,'sleeper_mean':10}]}]}
        surface_path.write_text(json.dumps(surface))
        integrated = w.bundle(root,2026,5,now,portfolio_surface=surface_path)
        observed = integrated['products']['EXPOSURE']['content']['captured_opponent_exposure']
        assert observed['players'][0]['player_id']=='gsis-1'
        assert observed['players'][0]['opponent_start_league_count']==1
        assert observed['capture_sha256']==w.digest(frozen)
        assert 'Observed H2H opponent starter exposure' in w.markdown(integrated)
        readiness = integrated['products']['EXPOSURE']['readiness']
        assert readiness['evidence']['submitted_opponent_player_count'] == 1
        assert readiness['evidence']['chopped_field_blocked_count'] == 1
        assert 'CHOPPED_ACTIVE_FIELD_NOT_CAPTURED' in readiness['blocking_reasons']
        assert all(row['complete'] is False and row['readiness']['certification'] == 'NOT_CERTIFIED' for row in integrated['products'].values())
        original=frozen.read_bytes()
        bad=dict(pr2);bad['generated_at']='2026-10-08T00:40:00Z';pr2_path.write_text(json.dumps(bad))
        assert w.bundle(root,2026,5,now)['sources']['PR2']['status']=='AVAILABLE'
        future=dict(pr2);future['generated_at']='2026-10-08T02:00:00Z';frozen.write_text(json.dumps(future))
        assert 'AFTER_LATEST' in w.bundle(root,2026,5,now)['sources']['PR2']['reason']
        frozen.write_bytes(original)
        bad=dict(pr2);bad['capture_id']='../escape';pr2_path.write_text(json.dumps(bad))
        assert 'IDENTITY_MISMATCH' in w.bundle(root,2026,5,now)['sources']['PR2']['reason']
        pr2_path.write_text(json.dumps(pr2));frozen.write_text('{}')
        assert 'REPLAY_MISMATCH' in w.bundle(root,2026,5,now)['sources']['PR2']['reason']
        frozen.write_bytes(original);frozen.unlink()
        assert 'CAPTURE_MISSING' in w.bundle(root,2026,5,now)['sources']['PR2']['reason']
        output = w.markdown(report)
        assert '0/7' in output and 'PARTIAL_OWNER_OUTPUT' in output and 'Product readiness evidence' in output
    root = Path(__file__).resolve().parents[1]
    actual = w.bundle(root, 2026, 4, w.stamp('2026-10-08T12:00:00Z'))
    performance = actual['products']['PLAYER_PERFORMANCE']
    evidence = performance['readiness']['evidence']
    assert evidence['scheduled_game_count'] == 16 and evidence['reported_team_count'] == 32
    assert evidence['player_game_count'] == 1110 and evidence['unresolved_source_row_count'] == 1
    assert 'SOURCE_PLAYER_ID_UNRESOLVED' in performance['readiness']['blocking_reasons']
    assert 'OFFICIAL_GAME_FINALITY_UNCERTIFIED' in performance['readiness']['blocking_reasons']
    assert actual['complete_product_count'] == 0
    print('PASS weekly report bundle: seven products, source lineage, exact target guards and evidence-specific readiness blockers')

if __name__ == '__main__':
    main()
