# Security and Privacy

## Deployment surface

Cloudflare deploys `dist/`, not repository root.

This prevents accidental publication of:

- Python source;
- archived docs;
- backup files;
- caches;
- full research intermediates.

## Personal portfolio mode

`tools/build_dist.py --mode personal` preserves the managed Sleeper portfolio configuration. Use this only for the owner's deployment. If the site should not be publicly discoverable, protect it with Cloudflare Access.

For a public/general deployment use:

```bash
python tools/build_dist.py --mode public
```

which emits an empty public portfolio config.

## Secrets

Do not store API secrets in repository files.

The browser diagnostics layer redacts common sensitive query parameters such as:

- `apiKey`
- `key`
- `token`
- `secret`
- authorization values.

The Odds key remains user-supplied/local and should not be logged.

## Proxy

Cloudflare data proxy routes are allowlisted. Upstream requests use a bounded timeout and sanitized error responses.

## Static headers

`dist/_headers` is generated from the source `_headers` policy. Review CSP whenever external sources or inline behavior change.
