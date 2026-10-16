from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
a2 = (ROOT / 'app' / 'v9.3.4a2-performance-hotfix.js').read_text(encoding='utf-8')
a3 = (ROOT / 'app' / 'v9.3.4a3-score-performance.js').read_text(encoding='utf-8')
store = (ROOT / 'app' / 'current-snapshot-store.js').read_text(encoding='utf-8')
contracts = (ROOT / 'functions' / 'api' / 'data' / 'nflverse' / 'contracts.js').read_text(encoding='utf-8')

checks = {
    'A3 release id': "const VERSION='9.3.4A3'" in a3,
    'A3 replaces assignScores': 'window.assignScores=fastAssignScores' in a3,
    'legacy score fallback retained': 'legacyAssign(reason)' in a3 and 'diagnostics.fallbacks++' in a3,
    'starter demand cached once': 'computeMarginalDemand' in a3 and 'demandMap()' in a3,
    'replacement indexed by position': 'fastReplacementLevels' in a3 and 'ownershipByPosition' in a3,
    'prediction caches built once': 'buildCycleCaches' in a3 and 'prediction-player-pass' in a3,
    'risk quantiles once per position': 'quantileSorted' in a3 and 'bands[pos]' in a3,
    'decision ranking one sort': 'fastDecisionScores' in a3 and 'rank.set(p,i)' in a3,
    'feature training removed from score critical path': 'featureLearningDeferred' in a3 and 'Deliberately do not train inside the score publication' in a3,
    'A3 diagnostics exposed': 'window.FIE934A3=' in a3 and "'934a3:assign-total'" in a3,
    'loader chains A3 after A2': 'a.onload=bootA3' in store and 'v9.3.4a3-score-performance.js' in store,
    'A2 keeps D/ST free agents': "if(has('DEF')||has('DST'))out.add('DEF');" in a2,
    'contracts uses live gzip asset': 'historical_contracts.csv.gz' in contracts,
    'contracts decompressed server side': "new DecompressionStream('gzip')" in contracts,
    'contracts returns csv': "Content-Type','text/csv" in contracts,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError('V9.3.4A3 integrity failures: ' + ', '.join(failed))

for rel in [
    'app/current-snapshot-store.js',
    'app/v9.3.4a2-performance-hotfix.js',
    'app/v9.3.4a3-score-performance.js',
]:
    subprocess.run(['node', '--check', str(ROOT / rel)], check=True)

print('V9.3.4A3 integrity: PASS')
