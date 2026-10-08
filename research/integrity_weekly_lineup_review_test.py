"""Replay chain, publication time and tampering regression checks."""
import json
import tempfile
from pathlib import Path
from integrity_in_season_pr2_lineup_outcome_test import capture_fixture
from adapt_in_season_pr2_lineup_outcome_stats import SOURCE_SCHEMA, adapt_source, source_identity
from build_in_season_pr2_lineup_outcome import build_outcome, write_outcome
from evaluate_in_season_pr2_lineups import evaluate_capture
from weekly_evidence_audit import stamp
from weekly_lineup_review import review


def main():
    from weekly_lineup_operational_evidence import head_to_head_context
    envelope={'captured_at':'2026-10-01T00:00:00Z','rows':[{'roster_id':1,'matchup_id':3},{'roster_id':2,'matchup_id':3,'starters':['100',0,'200']}]}
    before=json.dumps(envelope,sort_keys=True)
    context=head_to_head_context(1,envelope)
    observed=context['opponent_submitted_starters']
    assert observed['player_ids']==['100','200'] and observed['empty_slot_count']==1
    assert observed['player_id_namespace']=='sleeper' and not observed['final_lineup_certified']
    assert json.dumps(envelope,sort_keys=True)==before
    del envelope['rows'][1]['starters']
    assert head_to_head_context(1,envelope)['opponent_submitted_starters']['player_ids'] is None
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);capture=capture_fixture(root)
        base=root/'data/research/evaluation/2026/weeks/week-4/lineups'
        capture['generated_at']='2026-09-30T12:00:00Z'
        (base/'captures'/f"portfolio-{capture['capture_id']}.json").write_text(json.dumps(capture))
        stats={source_identity(c,'sleeper'):{'rushing_yards':50,'receptions':2} for c in capture['leagues'][0]['evaluation_input']['active_candidates']}
        source={'schema':SOURCE_SCHEMA,'season':2026,'week':4,'provider':'fixture','endpoint':'fixture',
                'observed_at':'2026-10-02T12:00:00Z','source_player_id_namespace':'sleeper',
                'sparse_zero_fields_are_explicit':True,'stats_by_source_player_id':stats}
        raw=adapt_source(capture,source);outcome=build_outcome(capture,raw,outcome_revision_id='final-v1')
        directory=base/'outcomes/final-v1';write_outcome(directory,outcome,raw)
        (directory/'raw-stats.json').write_text(json.dumps(raw))
        source_path=base/'outcomes/source-inputs/final-v1.json';source_path.parent.mkdir();source_path.write_text(json.dumps(source))
        evaluation_path=directory/'evaluation.json';evaluation_path.write_text(json.dumps(evaluate_capture(capture,outcome,root=root)))
        now=stamp('2026-10-03T12:00:00Z');due=stamp('2026-10-02T00:00:00Z')
        good=review(root,2026,4,now,due)
        assert len(good['revisions'])==1 and not good['blocked_revisions'] and not good['complete']
        assert good['paired_fie_sleeper_comparison']=='NOT_PROVIDED_BY_THIS_OWNER'
        before=evaluation_path.read_bytes();bad=json.loads(before);bad['aggregate']['lineup_regret']=999
        evaluation_path.write_text(json.dumps(bad))
        assert 'EVALUATION_REPLAY_MISMATCH' in review(root,2026,4,now,due)['blocked_revisions'][0]['reason']
        evaluation_path.write_bytes(before)
        assert 'TIME_INVALID' in review(root,2026,4,stamp('2026-10-02T11:00:00Z'),due)['blocked_revisions'][0]['reason']
        source_path.unlink()
        assert not review(root,2026,4,now,due)['revisions']
    print('PASS weekly lineup review: immutable source/scoring/evaluation replay, future outcomes and tampering rejected; no adoption or paired-model claim')

if __name__=='__main__':main()
