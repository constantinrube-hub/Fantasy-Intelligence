from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
a2 = (ROOT / 'app' / 'v9.3.4a2-performance-hotfix.js').read_text(encoding='utf-8')
store = (ROOT / 'app' / 'current-snapshot-store.js').read_text(encoding='utf-8')

checks = {
    'release id': "const VERSION='9.3.4A2'" in a2,
    'lean hot-path universe': 'leanPlayerMap' in a2 and 'wantedPositions' in a2 and 'rosteredIds' in a2,
    'inactive historical catalog filtered': "status==='active'" in a2 and 'search_rank' in a2,
    'draft controls lazy': 'installLazyDraft' in a2 and 'draftControlsDeferred' in a2,
    'core scoring deferred': 'coreAssignDeferred' in a2 and 'window.assignScores=function()' in a2,
    'core KPI deferred': 'coreKpisDeferred' in a2 and 'window.updateKPIs=function()' in a2,
    'core render coalesced': 'coreRendersDeferred' in a2 and 'afterPaint' in a2,
    'enhancements removed from critical path': 'pendingScope' in a2 and 'enhancementLaunches' in a2 and 'realEnhancements.call' in a2,
    'generation guard': 'sameContext' in a2 and 'currentGeneration' in a2,
    'progressive public status': 'installFetchCsvProgress' in a2 and 'publicSourceSettles' in a2,
    'canonical public counter': 'repairProgressDom' in a2 and 'Public Enrichment'.lower() in a2.lower(),
    'performance instrumentation': 'FIEPerformance' in a2 and 'core-interactive' in a2 and 'longFunctions' in a2,
    'runtime report exposed': 'window.FIE934A2=' in a2 and 'report' in a2,
    'store chains A2 after 9.3.4': 's.onload=bootA2' in store and 'v9.3.4a2-performance-hotfix.js' in store,
    'missing projection remains null': 'const pair=Array.isArray(proj[id])?proj[id]:null;' in store,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError('V9.3.4A2 integrity failures: ' + ', '.join(failed))

for rel in ['app/v9.3.4a2-performance-hotfix.js', 'app/current-snapshot-store.js']:
    subprocess.run(['node', '--check', str(ROOT / rel)], check=True)

print('V9.3.4A2 integrity: PASS')
