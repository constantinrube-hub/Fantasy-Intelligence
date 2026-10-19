#!/usr/bin/env python3
"""The generated browser policy must equal config/ui-decision-policy.json (deterministic)."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research'))
from generate_ui_policy import SRC, OUT, render, validate  # noqa: E402

policy = json.loads(SRC.read_text(encoding='utf-8'))
validate(policy)
assert OUT.exists(), 'run python research/generate_ui_policy.py'
assert OUT.read_text(encoding='utf-8') == render(policy), 'app/generated/ui-decision-policy.js is stale; regenerate'
body = re.search(r'deepFreeze\((\{.*\})\);\n\}\)\(\);', OUT.read_text(encoding='utf-8'), re.S).group(1)
assert json.loads(body) == policy, 'generated policy content differs from source'
print('UI decision policy: generated copy matches config/ui-decision-policy.json')
