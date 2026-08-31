#!/usr/bin/env python3
"""Build the canonical release component/hash manifest.
Run this only after code/config generation and immediately before dist build.

The manifest is intentionally reproducible. Its timestamp comes from the
canonical release descriptor rather than wall-clock build time so rebuilding an
unchanged release produces byte-identical deploy metadata.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COMPONENTS={
 'index':'index.html',
 'deployment_headers':'_headers',
 'release_descriptor':'config/release.json',
 'runtime_contract':'config/contracts/runtime-contracts.json',
 'runtime_contract_js':'app/generated/runtime-contracts.js',
 'model_config':'config/model-config.json',
 'model_config_js':'app/generated/model-config.js',
 'core_services':'app/core/core-services.js',
 'numeric_contract':'app/core/numeric.js',
 'season_context':'app/core/season-context.js',
 'projection_service':'app/core/projection-service.js',
 'draft_state_service':'app/core/draft-state-service.js',
 'surface_router':'app/core/surface-router.js',
 'special_teams_series':'app/core/special-teams-series.js',
 'draft_value_service':'app/core/draft-value-service.js',
 'data_client':'app/core/data-client.js',
 'cross_position_calibration':'app/core/value-calibration-guard.js',
 'research_report_service':'app/core/research-report-service.js',
 'research_report_ui':'app/research-report-ui.js',
 'research_value_finder_bridge':'app/core/research-value-finder-bridge.js',
 'current_snapshot_store':'app/current-snapshot-store.js',
 'decision_service':'app/core/decision-service.js',
 'runtime':'app/runtime-foundation.js',
 'current_player_features':'app/current-player-features.js',
 'decision_model':'app/decision-model-v9.js',
 'decision_engines':'app/decision-engines.js',
 'monte_carlo_worker':'app/draft-monte-carlo-worker.js',
 'value_finder':'app/value-finder.js',
 'portfolio_home':'app/portfolio-home.js',
 'portfolio_config':'app/portfolio-config.js',
 'dst_intelligence':'app/dst-intelligence.js',
 'kicker_intelligence':'app/kicker-intelligence.js',
 'league_context':'app/league-context.js',
 'decision_ui':'app/decision-ui.js',
 'decision_ui_css':'app/decision-ui.css',
 'league_profile':'research/league_profile.py',
 'dst_contract':'research/dst_contract.py',
 'dst_research':'research/fie_dst.py',
 'dst_integrity':'research/integrity_dst_test.py',
 'kicker_contract':'research/kicker_contract.py',
 'kicker_research':'research/fie_kicker.py',
 'kicker_integrity':'research/integrity_kicker_test.py',
 'scoring_relevance':'research/scoring_relevance.py',
 'current_snapshot_builder':'research/build_current_snapshot.py',
 'current_snapshot_storage':'research/current_snapshot_storage.py',
 'current_snapshot_deduper':'research/deduplicate_current_snapshots.py',
 'current_snapshot_storage_integrity':'research/integrity_current_storage_test.py',
 'league_app_snapshot_builder':'research/build_league_app_snapshots.py',
 'league_fast_switch_integrity':'research/integrity_league_fast_switch_test.py',
 'league_fast_switch_runtime_integrity':'research/integrity_league_fast_switch_runtime_test.js',
 'completion_15point_integrity':'research/integrity_15point_completion_test.py',
 'cross_position_calibration_integrity':'research/integrity_cross_position_calibration_test.js',
 'league_app_dist_sync':'tools/sync_league_app_snapshots.py',
 'research_pipeline_contract':'research/fie_research_pipeline_contract.py',
 'research_pipeline_runner':'research/run_fie_league_research_pipeline.py',
 'research_position_resolver':'research/resolve_fie_position_models.py',
 'research_final_board':'research/build_fie_final_league_board.py',
 'research_league_report':'research/build_fie_league_research_report.py',
 'research_portfolio_report':'research/build_fie_portfolio_research_report.py',
 'research_app_contract_publisher':'research/publish_fie_research_app_contract.py',
 'research_pipeline_integrity':'research/integrity_fie_research_pipeline_test.py',
 'research_app_contract_integrity':'research/integrity_fie_app_research_contract_test.js',
 'decision_validation':'research/decision_validation.py',
 'decision_validation_contract':'research/decision_validation_contract.json',
 'dist_builder':'tools/build_dist.py',
 'release_builder':'tools/release_build.py',
 'manifest_builder':'research/build_app_manifest.py',
 'build_determinism_integrity':'research/integrity_v932_build_determinism_test.py',
 'release_gate':'research/release_gate.py',
}
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def release_timestamp(release):
 ts=str(release.get('built_at') or '').strip()
 if not ts:raise ValueError('config/release.json built_at is required for deterministic build manifests')
 return ts
def build():
 release=json.loads((ROOT/'config/release.json').read_text());files={}
 for name,rel in COMPONENTS.items():
  p=ROOT/rel
  if not p.exists():raise FileNotFoundError(rel)
  files[name]={'path':rel,'sha256':sha(p),'bytes':p.stat().st_size}
 return {'schema_version':2,'app_version':release['release'],'runtime_version':release['runtime'],'draft_model_version':release['decision_model'],'value_finder_version':release['value_finder'],'research_generation':release['research_schema'],'model_promotion':json.loads((ROOT/'config/model-config.json').read_text()).get('production',{}),'runtime_research_scope':'league_namespaced_only','generated_at':release_timestamp(release),'files':files}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='config/build-manifest.json');a=ap.parse_args();out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(build(),indent=2)+'\n');print(out.relative_to(ROOT))
if __name__=='__main__':main()
