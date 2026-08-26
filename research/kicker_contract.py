#!/usr/bin/env python3
"""Canonical kicker scoring/profile contract for Fantasy Intelligence 9.2."""
from __future__ import annotations
import hashlib, json, math, re
from typing import Any, Iterable, Mapping
from generated_runtime_contracts import CONTRACTS

K_POSITION='K'
ALIASES=CONTRACTS.get('position_aliases') or {}
RULES=CONTRACTS.get('scoring_rule_families') or []
FG_BUCKET_RE=re.compile(r'^(fgm|fgmiss)_(0|([0-9]+)_([0-9]+)|([0-9]+)p)$')
K_EXACT={'fgm','fgmiss','fgm_yds','xpm','xpmiss'}


def canonical_position(position: str) -> str:
    p=str(position or '').upper(); return str(ALIASES.get(p,p))


def finite_nonzero(v: Any) -> bool:
    try: return math.isfinite(float(v)) and float(v)!=0
    except (TypeError,ValueError): return False


def kicker_starter_slots(roster_positions: Iterable[str]) -> int:
    return sum(1 for s in (roster_positions or []) if canonical_position(str(s))==K_POSITION)


def kicker_enabled(roster_positions: Iterable[str]) -> bool:
    return kicker_starter_slots(roster_positions)>0


def is_kicker_scoring_key(key: str) -> bool:
    k=str(key or '').lower()
    return k in K_EXACT or FG_BUCKET_RE.match(k) is not None


def kicker_scoring_settings(scoring: Mapping[str,Any]) -> dict[str,float]:
    return dict(sorted((str(k),float(v)) for k,v in (scoring or {}).items() if finite_nonzero(v) and is_kicker_scoring_key(str(k))))


def kicker_scoring_signature(scoring: Mapping[str,Any]) -> str:
    raw=json.dumps(kicker_scoring_settings(scoring),sort_keys=True,separators=(',',':'),ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def kicker_roster_signature(roster_positions: Iterable[str], total_rosters: Any=None, fmt: str|None=None, position_limits: Mapping[str,Any]|None=None) -> str:
    try: teams=int(total_rosters or 0)
    except (TypeError,ValueError): teams=0
    lim=(position_limits or {}).get('K') if isinstance(position_limits,Mapping) else None
    payload={'starter_slots':kicker_starter_slots(roster_positions),'total_rosters':teams,'format':str(fmt or ''),'k_limit':lim}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:16]


def kicker_profile_fields(profile: Mapping[str,Any]) -> dict[str,Any]:
    slots=profile.get('roster_positions') or []; scoring=profile.get('scoring_settings') or {}
    return {
      'kicker_enabled':kicker_enabled(slots),'kicker_starter_slots':kicker_starter_slots(slots),
      'kicker_scoring_settings':kicker_scoring_settings(scoring),'kicker_scoring_signature':kicker_scoring_signature(scoring),
      'kicker_roster_signature':kicker_roster_signature(slots,profile.get('total_rosters'),profile.get('format'),profile.get('position_limits') or {}),
    }
