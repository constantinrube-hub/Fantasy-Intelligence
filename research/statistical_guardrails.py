"""Shared V8.9 promotion guardrails.

Promotion is based on paired chronological holdout improvements, not in-sample fit.
The bootstrap resamples whole temporal folds (season blocks), preserving within-fold
correlation instead of treating player-weeks as independent observations.
"""
from __future__ import annotations
import math
from typing import Iterable, Optional, Sequence
import numpy as np


def _finite(xs: Iterable[float]) -> list[float]:
    out=[]
    for x in xs:
        try:
            v=float(x)
        except Exception:
            continue
        if math.isfinite(v): out.append(v)
    return out


def temporal_block_bootstrap_ci(improvements: Sequence[float], weights: Optional[Sequence[float]]=None, *, iterations: int=4000, seed: int=89) -> tuple[Optional[float], Optional[float]]:
    vals=_finite(improvements)
    if len(vals)<3: return None,None
    if weights is None:
        w=np.ones(len(vals),dtype=float)
    else:
        raw=list(weights)
        w=np.array([float(raw[i]) if i<len(raw) and math.isfinite(float(raw[i])) and float(raw[i])>0 else 1.0 for i in range(len(vals))],dtype=float)
    a=np.array(vals,dtype=float)
    rng=np.random.default_rng(seed)
    means=np.empty(iterations,dtype=float)
    n=len(a)
    for i in range(iterations):
        idx=rng.integers(0,n,size=n)
        means[i]=float(np.average(a[idx],weights=w[idx]))
    lo,hi=np.quantile(means,[.025,.975])
    return float(lo),float(hi)


def promotion_gate(improvements: Sequence[float], *, weights: Optional[Sequence[float]]=None, min_mean: float=.01, win_share: float=.67, min_folds: int=4, require_positive_ci: bool=True) -> dict:
    vals=_finite(improvements)
    mean=float(np.average(vals,weights=np.array(weights[:len(vals)],dtype=float))) if vals and weights is not None and len(weights)>=len(vals) else (float(np.mean(vals)) if vals else None)
    wins=sum(v>0 for v in vals)
    need=max(2,int(math.ceil(len(vals)*win_share))) if vals else 0
    lo,hi=temporal_block_bootstrap_ci(vals,weights=weights)
    ok=(len(vals)>=min_folds and mean is not None and mean>=min_mean and wins>=need and (not require_positive_ci or (lo is not None and lo>0)))
    return {"mean":mean,"positive_folds":wins,"required_positive_folds":need,"ci95_low":lo,"ci95_high":hi,"robust":bool(ok),"folds":len(vals)}
