# V8.9-VF1 Value Finder Changelog

## Added
- New **Draft → Value Finder** sub-tab.
- ADP bands: `<100`, `100–150`, `150–200`, combined `100–200`, `200+`, and all ADP.
- League-eligible, same-position Sleeper market ranks. Hard-excluded players never affect the comparison, including Genesis 2025+ eligibility.
- Preseason M5 policy score calculated independently of the live M6 activation gate, using the active league format's M5 draft weights and renormalizing missing components.
- **Snap Path Score** combining current opportunity, live Sleeper depth order, curated role/path evidence, and injury status.
- 200+ deep-sleeper mode weights snap-path certainty most heavily and fail-filters weak speculative paths by default.
- Historical M5 position-level draft validation shown as evidence and incorporated into confidence.
- High / Medium / Low target confidence.
- Dynamic target windows derived from Sleeper ADP, positional edge, role certainty and confidence.
- Live target states: `WATCH`, `WAIT`, `TARGET`, `TAKE NOW`, `DRAFTED`.
- Filters for ADP range, position, snap path, experience, confidence, FIE-undervalued-only, undrafted-only, and result count.
- Sortable Value Finder table.
- Player rows open the existing detailed player drawer.

## Draft Assistant integration
- Added **Value Finder** and **Target plan** columns without replacing existing Draft Assistant recommendation logic.
- Late targets display ADP band, Snap Path Score, positional divergence, target range and live survival-aware state.
- Existing opponent-aware manager pressure and survival model remain authoritative for the Draft Assistant's original recommendation.

## Governance
- M6 is not force-enabled or bypassed.
- Value Finder reads M5 research/current artifacts only as preseason/draft evidence.
- M5 bundle getter methods were exposed so the UI can reuse already-loaded artifacts without duplicate multi-megabyte fetches.
- Missing policy inputs are renormalized, consistent with M5 `m5Weighted` behavior.

## Important interpretation
- Value Finder is a **discovery layer**: “who should I circle ahead of market cost?”
- Draft Assistant remains the **execution layer**: “who should I select right now?”
- Draft Player Analysis remains the **opponent/market history layer**: “how does this league actually draft?”
