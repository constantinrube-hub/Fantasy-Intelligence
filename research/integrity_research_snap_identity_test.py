"""Identity collisions, cutoff leakage and missing units remain fail closed."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from research_snap_identity import bind, build
from research_source_archive import archive


def reject(action):
    try:
        action()
    except ValueError:
        return
    raise AssertionError('invalid identity evidence accepted')


def main():
    source = [{'source_pfr_player_id': 'pfr:one', 'offense_snaps': 40},
              {'source_pfr_player_id': 'pfr:missing', 'offense_snaps': 0},
              {'source_pfr_player_id': 'pfr:bad', 'offense_snaps': None}]
    original = deepcopy(source)
    identity = [{'pfr_id': 'one', 'gsis_id': '00-0000001'}, {'pfr_id': 'bad', 'gsis_id': 'NAME:one'}]
    report = bind(source, identity)
    assert report['rows'][0]['canonical_player_id'] == '00-0000001'
    assert report['rows'][1]['identity_status'] == 'BLOCKED_PFR_ID_UNMAPPED'
    assert report['rows'][2]['identity_status'] == 'BLOCKED_GSIS_IDENTITY'
    assert source == original and report['rows'][1]['offense_snaps'] == 0
    assert report['rows'][2]['offense_snaps'] is None
    assert all(r['offense_snap_share'] is None and r['percentage_scale'] == 'UNVERIFIED' for r in report['rows'])
    reject(lambda: bind(source, identity + [identity[0]]))
    reject(lambda: bind([{'source_pfr_player_id': 'pfr:one', 'game_id': 'g'},
                         {'source_pfr_player_id': 'pfr:alias', 'game_id': 'g'}],
                        identity + [{'pfr_id': 'alias', 'gsis_id': '00-0000001'}]))
    reject(lambda: bind([{'source_pfr_player_id': 'one'}], identity))
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        raw = b'game_id,season,week,game_type,pfr_player_id,team,offense_snaps\ng,2026,1,REG,one,A,40\n'
        snaps = archive(root, 'snaps', 2026, raw, '2026-09-15T12:00:00Z')
        ids = archive(root, 'identity', 2026, b'pfr_id,gsis_id\none,00-0000001\n', '2026-09-16T12:00:00Z')
        reject(lambda: build(root, snaps, ids, season=2026, target_week=2, cutoff='2026-09-15T13:00:00Z'))
        result = build(root, snaps, ids, season=2026, target_week=2, cutoff='2026-09-17T12:00:00Z')
        assert result['identity_status_counts'] == {'CANONICAL_GSIS_BOUND': 1}
        (ids.parent / 'source.csv').write_bytes(b'pfr_id,gsis_id\none,00-0000002\n')
        reject(lambda: build(root, snaps, ids, season=2026, target_week=2, cutoff='2026-09-17T12:00:00Z'))
    print('PASS source-bound canonical snap identity, duplicates, missingness, units and observation cutoff')


if __name__ == '__main__':
    main()
