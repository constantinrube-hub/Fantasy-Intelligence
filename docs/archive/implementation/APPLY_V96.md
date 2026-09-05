# Apply V9.6

1. Upload every file in this patch to the matching repository path.
2. Replace `.github/workflows/build-fie-current.yml` with the included version.
3. Run **Build FIE V9.6 Runtime Bundle** for each league you want to promote.
4. For the first league use the same inputs as the successful shadow run: league `1391803939736801280`, format `REDRAFT`, report season `2026`, history `2016-2025`.
5. Validate that the runtime workflow succeeds and commits `performance/2026/runtime/v96_runtime.json` plus `v96_runtime_models.joblib`.
6. Run **Refresh FIE Current Season**. During preseason V9.6 should report a blocked status and make zero projection changes. Once valid 2026 completed-game features exist, eligible QB/RB weekly projections may use V9.6 automatically.

Leagues without a V9.6 runtime bundle remain canonical.
