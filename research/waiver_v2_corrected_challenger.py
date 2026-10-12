"""Exploratory corrected-source replay of the unchanged frozen Ridge protocol."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from build_waiver_v2_label_batch import digest
from waiver_v2_validation import features, evaluate, keyed, policy, POLICY

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'config/waiver-v2-corrected-label-challenger.json'


def build(population_report,frozen_report,output_dir):
    if output_dir.exists():raise ValueError('WAIVER_CORRECTED_OUTPUT_MUST_BE_NEW')
    population=json.loads(population_report.read_text());frozen=json.loads(frozen_report.read_text())
    if digest(frozen_report)!=population['frozen_validation_report']['sha256']:
        raise ValueError('WAIVER_CORRECTED_FROZEN_REPORT_CHANGED')
    if not population['global_identity_closure'] or population['activation_eligible'] is not False:
        raise ValueError('WAIVER_CORRECTED_WRONG_POPULATION_REVISION')
    contract=policy();prepared=[]
    for original in frozen['units']:
        signature,position=original['scoring_signature'],original['position']
        profile=next(row for row in population['profiles'] if row['scoring_signature']==signature)
        label_path=population_report.parent/Path(profile['expanded_labels']['path']).name
        if digest(label_path)!=profile['expanded_labels']['sha256']:raise ValueError('WAIVER_CORRECTED_LABEL_CHANGED')
        labels=pd.read_csv(label_path,low_memory=False)
        stats_path=frozen_report.parent/'sources'/Path(original['source_inputs']['player_stats']['path']).name
        if digest(stats_path)!=original['source_inputs']['player_stats']['sha256']:raise ValueError('WAIVER_CORRECTED_RAW_FEATURE_CHANGED')
        old_features_path=frozen_report.parent/Path(original['artifacts']['features']['path']).name
        if digest(old_features_path)!=original['artifacts']['features']['sha256']:raise ValueError('WAIVER_CORRECTED_CUTOFF_UNIVERSE_CHANGED')
        old_features=pd.read_csv(old_features_path)
        # Target-only rows are available to past-score lookups, never cutoffs.
        candidate_features=features(labels,pd.read_csv(stats_path,low_memory=False),position,contract)
        frame=keyed(candidate_features).loc[keyed(old_features).index].reset_index(drop=True)
        prepared.append((original,profile,labels,frame))
    output_dir.mkdir(parents=True);units=[]
    for original,profile,labels,frame in prepared:
        result,predictions,models=evaluate(frame,labels,contract)
        name=f'{original["scoring_signature"]}-{original["position"]}'
        artifacts={}
        for kind,data in [('features',frame),('predictions',predictions)]:
            path=output_dir/f'{name}-{kind}.csv.gz';data.to_csv(path,index=False,compression={'method':'gzip','mtime':0})
            artifacts[kind]={'path':str(path),'sha256':digest(path),'rows':len(data)}
        model_path=output_dir/f'{name}-fold-models.json'
        model_path.write_text(json.dumps(models,indent=2,sort_keys=True,allow_nan=False)+'\n')
        artifacts['fold_models']={'path':str(model_path),'sha256':digest(model_path)}
        units.append({'scoring_signature':original['scoring_signature'],'position':original['position'],
                      'expanded_labels':profile['expanded_labels'],'original_cutoff_features':original['artifacts']['features'],
                      'raw_feature_inputs':original['source_inputs']['player_stats'],'artifacts':artifacts,
                      'research_interpretation':'REUSED_HOLDOUT_CORRECTED_SOURCE_REPLAY','independent_confirmation':False,**result})
    report={'schema':'fie-waiver-v2-corrected-source-challenger-v1','diagnostic_only':True,'activation_eligible':False,
            'builder_sha256':digest(Path(__file__)),'feature_validation_owner_sha256':digest(Path(__file__).with_name('waiver_v2_validation.py')),
            'methodology':{'path':str(POLICY),'sha256':digest(POLICY)},'corrected_contract':{'path':str(CONTRACT),'sha256':digest(CONTRACT)},
            'population_report':{'path':str(population_report),'sha256':digest(population_report)},
            'frozen_report':{'path':str(frozen_report),'sha256':digest(frozen_report)},'units':units,
            'research_signal_units':sum(u['research_signal_passed'] for u in units),'eligible_forecast_units':0,
            'independent_confirmation':False,'hyperparameter_grid_changed':False,
            'limitations':['All four outer seasons are reused research evidence; no independent confirmation.',
                           'Some 2018 source weeks remain incomplete. Publication timing, live parity and promotion remain blocked.',
                           'No raw opportunity zero, new cutoff identity or transaction has been invented.']}
    (output_dir/'corrected-challenger-report.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--population-report',type=Path,required=True)
    p.add_argument('--frozen-report',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    r=build(args.population_report,args.frozen_report,args.output_dir)
    print(json.dumps({'units':len(r['units']),'research_signal_units':r['research_signal_units'],'eligible_forecast_units':0,'independent_confirmation':False}))


if __name__=='__main__':main()
