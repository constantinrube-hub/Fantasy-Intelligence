# V9.7.3 workflow rebase hotfix

The V9.7.3 research build and validation succeeded. The failure occurred only in the
final Git rebase because the broad M7-M9 cache restore left unrelated tracked files
modified but unstaged.

Replace:
- `.github/workflows/build-fie-strategy-stack.yml`

Recommended for repository consistency:
- `research/build-fie-strategy-stack.yml`

Then rerun **Build FIE Strategy Research Stack** with the same inputs.

No Python/model files need to be replaced.
No market or availability capture workflow needs to be rerun separately.

The corrected final step prints `Post-commit worktree status:` and discards only
remaining unstaged tracked cache side-effects after the intended outputs have already
been committed. Unexpected staged changes still fail closed.
