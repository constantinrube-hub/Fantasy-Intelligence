#!/usr/bin/env python3
"""All-game scope, raw source tampering, missing fields and postgame timing."""
import csv,gzip,hashlib,io,json,tempfile
from unittest.mock import patch
from pathlib import Path
from point_in_time_capture import build_envelope,canonical_bytes
from weekly_evidence_audit import stamp
import weekly_player_performance as w


def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);schedule=root/'data/research/context/weather/2026/week_04/a/schedule-source-envelope.json';schedule.parent.mkdir(parents=True)
        payload={'season':2026,'week':4,'games':[{'game_id':'game','home_team':'AAA','away_team':'BBB','kickoff':'2026-10-05T17:00:00Z'}]}
        schedule.write_text(json.dumps({'observed_at':'2026-10-01T00:00:00Z','payload':payload,'payload_sha256':hashlib.sha256(canonical_bytes(payload)).hexdigest()}))
        rows=[{'player_id':'a','player_display_name':'A','season':'2026','week':'4','season_type':'REG','game_id':'game','team':'AAA','targets':'5','receptions':'3','fantasy_points_ppr':'8'},
              {'player_id':'b','player_display_name':'B','season':'2026','week':'4','season_type':'REG','game_id':'game','team':'BBB','targets':'0','receptions':'0','fantasy_points_ppr':'0'}]
        data=io.StringIO();writer=csv.DictWriter(data,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows);raw=data.getvalue().encode()
        path=root/'raw.csv.gz';path.write_bytes(gzip.compress(raw,mtime=0))
        source=root/'source.json';source.write_text(json.dumps(build_envelope(capture_id='test',capture_intent='OTHER_GOVERNED',provider='fixture',endpoint='fixture',observed_at='2026-10-06T06:00:00Z',as_of_semantics='retrospective',payload={'season':2026,'week':4,'rows':w.target_rows(raw,2026,4),'raw_path':'raw.csv.gz','raw_response_sha256':hashlib.sha256(raw).hexdigest(),'raw_archive_sha256':w.digest(path)})))
        with patch.object(w,'capture',side_effect=AssertionError('No capture is allowed before completion')):
            assert w.ensure_completed(root,2026,4,stamp('2026-10-06T04:59:00Z'))['status']=='NO_OP_NO_STORED_COMPLETED_WEEK'
        due=w.build(root,source,2026,4,stamp('2026-10-06T04:59:00Z'));assert due['status']=='NOT_DUE' and due['games']==[]
        ready=w.build(root,source,2026,4,stamp('2026-10-06T07:00:00Z'))
        assert ready['game_count']==1 and ready['player_game_count']==2 and ready['status']=='AVAILABLE_PROVIDER_ROWS'
        metric=ready['games'][0]['teams'][0]['players'][0]['metrics'];assert metric['fantasy_points_ppr']==0 and metric['passing_yards'] is None
        assert ready['governance']['pregame_feature_eligible'] is False and ready['governance']['official_game_finality_certified'] is False
        assert 'AAA' in w.markdown(ready) and 'BBB' in w.markdown(ready)
        try:
            w.build(root,source,2026,4,stamp('2026-10-06T05:30:00Z'));raise AssertionError('Future source accepted')
        except ValueError as exc:assert 'AFTER_AS_OF' in str(exc)
        path.write_bytes(path.read_bytes()+b'tamper')
        try:
            w.build(root,source,2026,4,stamp('2026-10-06T07:00:00Z'));raise AssertionError('Raw tamper accepted')
        except ValueError as exc:assert 'HASH_MISMATCH' in str(exc)
    print('PASS player performance: all-game/team scope, missing versus zero, stabilization, future-source exclusion, immutable raw hash, retrospective-only authority')

if __name__=='__main__':main()
