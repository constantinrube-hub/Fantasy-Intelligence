# Apply V9.3.4A-B

This archive contains repository-relative paths. Copy the listed `app`, `research`, `tools` and `.github` files over the same paths in Fantasy-Intelligence.

Base commit used to build the patch:

`dbe35983a9932a4e5ba540dc4606e5f4215055cb`

Do not replace unrelated files or the repository wholesale.

After the source commit:

1. Run **Validate FIE V9.3.4A-B**.
2. Run **Refresh FIE Current Season** once. The new shared player catalog is a generated artifact and must be built before the cold-load fast path can be measured in production.
3. Wait for the refreshed `dist` commit and Cloudflare deployment.
4. Perform the timing and correctness QA in `RELEASE_NOTES_V9.3.4A-B.md`.

If `main` has moved beyond the base commit before you apply this package, compare the eight paths before overwriting them. Generated current-data commits that only touch data/dist are normally safe, but source changes to any of these eight paths should be merged rather than blindly replaced.
