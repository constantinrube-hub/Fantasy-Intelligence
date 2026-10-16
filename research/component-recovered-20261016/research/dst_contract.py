#!/usr/bin/env python3
"""Stdlib-only canonical D/ST contract helpers shared by profile, research and tests."""
from __future__ import annotations
import hashlib, json, math, re
from typing import Any, Iterable, Mapping
from generated_runtime_contracts import CONTRACTS

DST_POSITION='DEF'
DST_SCORING_EXACT={
 'blk_kick','blk_kick_ret_yd','def_4_and_stop','def_pass_def','def_td','ff','fum_rec','fum_rec_yd','fum_ret_yd','int','int_ret_yd','sack','sack_yd','safe',
 'def_st_td','def_st_ff','def_st_fum_rec','def_kr_yd','def_pr_yd','def_fg_ret_yd'
}
PTS_ALLOW_RE=re.compile(r'^pts_allow_(0|([0-9]+)_([0-9]+)|([0-9]+)p)$')
YDS_ALLOW_RE=re.compile(r'^yds_allow_(0|([0-9]+)_([0-9]+)|([0-9]+)p)$')
ALIASES=CONTRACTS.get('position_aliases') or {}
RULES=CONTRACTS.get('scoring_rule_families') or []


def canonical_position(position: str) -> str:
    p=str(position or '').upper(); return str(ALIASES.get(p,p))


def _matches(rule: Mapping, key: str) -> bool:
    k=str(key or '').lower(); kind=rule.get('match'); pattern=rule.get('pattern')
    if kind=='exact': return k==str(pattern).lower()
    if kind=='prefix': return k.startswith(str(pattern).lower())
    if kind=='regex': return re.search(str(pattern),k,re.I) is not None
    if kind=='exact_set': return k in {str(x).lower() for x in (pattern or [])}
    return False


def rule_spec(key: str) -> dict|None:
    for r in RULES:
        if _matches(r,key): return dict(r)
    return None


def finite_nonzero(v: Any) -> bool:
    try: return math.isfinite(float(v)) and float(v)!=0
    except (TypeError,ValueError): return False


def dst_starter_slots(roster_positions: Iterable[str]) -> int:
    return sum(1 for s in (roster_positions or []) if canonical_position(str(s))==DST_POSITION)


def dst_enabled(roster_positions: Iterable[str]) -> bool:
    return dst_starter_slots(roster_positions)>0


def is_dst_scoring_key(key: str) -> bool:
    spec=rule_spec(str(key))
    if spec and DST_POSITION in {canonical_position(x) for x in (spec.get('positions') or [])}: return True
    k=str(key).lower(); return bool(k in DST_SCORING_EXACT or PTS_ALLOW_RE.match(k) or YDS_ALLOW_RE.match(k))


def dst_scoring_settings(scoring: Mapping[str,Any]) -> dict[str,float]:
    out={}
    for k,v in (scoring or {}).items():
        if not finite_nonzero(v) or not is_dst_scoring_key(str(k)): continue
        out[str(k)]=float(v)
    return dict(sorted(out.items()))


def dst_scoring_signature(scoring: Mapping[str,Any]) -> str:
    raw=json.dumps(dst_scoring_settings(scoring),sort_keys=True,separators=(',',':'),ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def dst_roster_signature(roster_positions: Iterable[str], total_rosters: Any=None, fmt: str|None=None) -> str:
    try: teams=int(total_rosters or 0)
    except (TypeError,ValueError): teams=0
    payload={'starter_slots':dst_starter_slots(roster_positions),'total_rosters':teams,'format':str(fmt or '')}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:16]


def dst_profile_fields(profile: Mapping[str,Any]) -> dict[str,Any]:
    slots=profile.get('roster_positions') or []; scoring=profile.get('scoring_settings') or {}
    return {
      'dst_enabled':dst_enabled(slots),'dst_starter_slots':dst_starter_slots(slots),
      'dst_scoring_settings':dst_scoring_settings(scoring),'dst_scoring_signature':dst_scoring_signature(scoring),
      'dst_roster_signature':dst_roster_signature(slots,profile.get('total_rosters'),profile.get('format')),
    }
