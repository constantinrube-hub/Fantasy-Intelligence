#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=(ROOT/'research/build_fie_portfolio_research_report.py').read_text(encoding='utf-8')
assert "enabled_league_rows()" in p
assert "cross_league_validation_pooling':False" in p
assert "automatic_promotion':False" in p
assert "counts['completed']+counts['blocked']+counts['failed']==enabled" in p
print('PASS portfolio completeness/no-pooling contract')
