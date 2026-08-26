# FIE V8.9-VF1 · Draft Value Finder

## What changed
The Draft workspace now has four complementary surfaces:

1. **Draft Board**: broad league-specific ranking universe.
2. **Value Finder**: identifies players the model wants targeted ahead of Sleeper market cost.
3. **Draft Player Analysis**: learns actual league/manager drafting behavior from imported drafts.
4. **Draft Assistant**: live pick execution, roster fit, survival and opponent pressure.

## Value Finder modes
- **ADP 100–200**: valuation/mispricing emphasis.
- **ADP 200+**: snap-path-first deep sleeper screen.
- Additional bands: <100, 100–150, 150–200, All.

## Main fields
- Sleeper overall ADP
- eligible same-position Sleeper market rank
- FIE preseason M5 policy rank
- positional edge
- M5 policy score and input coverage
- Snap Path Score
- historical position-level M5 draft evidence
- Target Strength
- confidence
- target window
- live WATCH / WAIT / TARGET / TAKE NOW / DRAFTED state

## Genesis handling
Value Finder builds market ranks from the existing league-eligible pool. Hard-excluded experience classes therefore never affect the comparison. Roster-level caps remain acquisition constraints rather than global player exclusions.

## M6 governance
Value Finder does **not** force M6 on. It uses M5 preseason/draft evidence independently of the weekly production gate. Production M6 remains governed exactly as before.

## Deployment
Because Value Finder is a separate module, deploy/commit both:
- `index.html`
- `app/value-finder.js`

For a GitHub/Cloudflare Pages deployment, commit the full repository contents from this release zip. No new Cloudflare configuration or build command is required.
