# Release Checklist

## Source correctness

- [ ] Runtime contracts regenerated.
- [ ] Model config regenerated.
- [ ] Release descriptor regenerated.
- [ ] Structural league profiles are consistent.
- [ ] Saved league B cannot mutate active league A.
- [ ] Rapid switch race test passes.
- [ ] 3RR test passes.
- [ ] Replacement cutoff is league-wide.
- [ ] Exact roster marginal uses FLEX/SF legality.
- [ ] Monte Carlo preserves owned players.
- [ ] Monte Carlo bench excludes starters.
- [ ] Value Finder consumes canonical production decision source.
- [ ] Research features cannot bypass governance.

## Release package

- [ ] Build manifest generated last.
- [ ] Build-manifest integrity PASS.
- [ ] `dist/` regenerated.
- [ ] No Python/docs/backups/caches in `dist/`.
- [ ] Deployment mode is intentional: personal or public.
- [ ] No secrets in static files or diagnostics.
- [ ] Release versions agree.

## Automated gates

- [ ] `python research/production_readiness.py` PASS.
- [ ] `python research/release_gate.py` PASS.
- [ ] Deep research validation PASS or explicitly not required for this source-only change.

## Browser preview

- [ ] Cold load.
- [ ] Cached load.
- [ ] Redraft.
- [ ] Chopped.
- [ ] Dynasty/Best Ball/SF representative fixtures.
- [ ] A→B→A switching.
- [ ] Saved format isolation.
- [ ] Draft Assistant.
- [ ] Value Finder.
- [ ] Monte Carlo + cancel.
- [ ] Lab status truth.
- [ ] Mobile viewport.

## Production

- [ ] Preview is clean.
- [ ] Production release is tagged/committed.
- [ ] Cloudflare health endpoint reports the same release version.
