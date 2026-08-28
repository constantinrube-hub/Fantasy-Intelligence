#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rel=json.loads((R/'config/release.json').read_text());manifest=json.loads((R/'config/build-manifest.json').read_text());model=json.loads((R/'config/model-config.json').read_text())
assert manifest['app_version']==rel['release'];assert manifest['runtime_version']==rel['runtime'];assert rel['decision_model']==model['model_version']
assert rel['release'] in (R/'app/generated/release.js').read_text();assert 'FIE_RELEASE.release' in (R/'functions/api/health.js').read_text();assert 'FIE_RELEASE.release' in (R/'functions/api/data/[[path]].js').read_text()
sys.path.insert(0,str(R/'research'))
from integrity_app_shell_test import validate_source,validate_dist
validate_source();validate_dist()
print('PASS integrity_release_versions_test + production shell parity')
