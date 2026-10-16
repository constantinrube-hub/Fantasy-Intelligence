#!/usr/bin/env python3
"""Canonical position-aware Sleeper scoring relevance.

The source of truth is config/contracts/runtime-contracts.json. Browser and
research code consume generated views of the same contract.
"""
from __future__ import annotations
import re
from typing import Iterable, Mapping
from generated_runtime_contracts import CONTRACTS, CONTRACT_SHA256

SLOTS=CONTRACTS.get('roster_slots') or {}
ALIASES=CONTRACTS.get('position_aliases') or {}
RULES=CONTRACTS.get('scoring_rule_families') or []


def canonical_position(position: str) -> str:
    p=str(position or '').upper()
    return str(ALIASES.get(p,p))


def roster_positions(slots: Iterable[str]) -> set[str]:
    out=set()
    for s in slots or []:
        spec=SLOTS.get(str(s).upper()) or {}
        out.update(canonical_position(x) for x in (spec.get('positions') or []))
    return out


def _matches(rule: Mapping, key: str) -> bool:
    k=str(key or '').lower();kind=rule.get('match');pattern=rule.get('pattern')
    if kind=='exact': return k==str(pattern).lower()
    if kind=='prefix': return k.startswith(str(pattern).lower())
    if kind=='regex': return re.search(str(pattern),k,re.I) is not None
    if kind=='exact_set': return k in {str(x).lower() for x in (pattern or [])}
    return False


def rule_spec(key: str) -> dict | None:
    for rule in RULES:
        if _matches(rule,key): return dict(rule)
    return None


def relevant_positions_for_rule(key: str) -> set[str] | None:
    spec=rule_spec(key)
    if not spec:
        # Unknown rules remain relevant instead of being silently hidden.
        return None
    return {canonical_position(x) for x in (spec.get('positions') or [])}


def rule_relevant(key: str, rosterable: set[str]) -> bool:
    p=relevant_positions_for_rule(key)
    return True if p is None else bool(p & {canonical_position(x) for x in rosterable})


def position_relevant(key: str, position: str) -> bool:
    p=relevant_positions_for_rule(key)
    return True if p is None else canonical_position(position) in p


def rule_metadata(key: str) -> dict:
    spec=rule_spec(key)
    if not spec:
        return {'key':str(key),'family':'UNKNOWN','entity':'unknown','positions':None,'contract_sha256':CONTRACT_SHA256}
    return {'key':str(key),'family':spec.get('id'),'entity':spec.get('entity'),'positions':sorted(relevant_positions_for_rule(key) or []),'weekly_supported':spec.get('weekly_supported'),'season_supported':spec.get('season_supported'),'contract_sha256':CONTRACT_SHA256}


def relevant_scoring_audit(scoring: Mapping, audit: Mapping, roster_slots: Iterable[str]) -> dict:
    rosterable=roster_positions(roster_slots)
    unsupported_rows=list(audit.get('unsupported') or [])
    unsupported_map={str(x.get('key')):x for x in unsupported_rows if isinstance(x,dict)}
    unsupported_map.update({str(x):{'key':str(x),'reason':'unsupported'} for x in unsupported_rows if isinstance(x,str)})
    nonzero=[str(k) for k,v in (scoring or {}).items() if _finite_nonzero(v)]
    relevant=[k for k in nonzero if rule_relevant(k,rosterable)]
    ignored=[k for k in nonzero if k not in relevant]
    unsupported=[{**unsupported_map[k],**rule_metadata(k)} for k in relevant if k in unsupported_map]
    supported=[k for k in relevant if k not in unsupported_map]
    unknown=[k for k in relevant if rule_spec(k) is None]
    return {
        'contract_sha256':CONTRACT_SHA256,
        'rosterable_positions':sorted(rosterable),'nonzero_keys':len(nonzero),'relevant_nonzero_keys':len(relevant),
        'supported_keys':sorted(supported),'unsupported':unsupported,'unknown_relevant':sorted(unknown),'ignored_irrelevant':sorted(ignored),
        'coverage_rate':len(supported)/len(relevant) if relevant else 1.0,'exact_replay_eligible':not unsupported,
    }


def position_support(scoring: Mapping, audit: Mapping, position: str) -> dict:
    unsupported_rows=list(audit.get('unsupported') or [])
    um={str(x.get('key')):x for x in unsupported_rows if isinstance(x,dict)}
    um.update({str(x):{'key':str(x),'reason':'unsupported'} for x in unsupported_rows if isinstance(x,str)})
    relevant=[str(k) for k,v in (scoring or {}).items() if _finite_nonzero(v) and position_relevant(str(k),position)]
    unsupported=[{**um[k],**rule_metadata(k)} for k in relevant if k in um]
    unknown=[k for k in relevant if rule_spec(k) is None]
    return {'contract_sha256':CONTRACT_SHA256,'position':canonical_position(position),'relevant_keys':len(relevant),'unsupported':unsupported,'unknown_relevant':unknown,'exact':not unsupported,'coverage_rate':(len(relevant)-len(unsupported))/len(relevant) if relevant else 1.0}


def _finite_nonzero(v):
    try: return float(v)!=0
    except (TypeError,ValueError): return False
