"""Conservative scoring certification for archived raw Sleeper means only."""
from __future__ import annotations

import math
from scoring_relevance import canonical_position, position_relevant, rule_spec

# Only additive event/count rules. Nonlinear thresholds and pre-scored points
# deliberately have no entry, even when the payload happens to contain them.
ALIASES = {
    'pass_yd': ('passing_yards',), 'pass_td': ('passing_tds',),
    'pass_int': ('interceptions', 'passing_interceptions'),
    'pass_cmp': ('completions',), 'pass_att': ('attempts', 'passing_attempts'),
    'pass_2pt': (), 'rush_yd': ('rushing_yards',), 'rush_td': ('rushing_tds',),
    'rush_att': ('carries', 'rushing_attempts'), 'rush_2pt': (),
    'rec': ('receptions',), 'rec_yd': ('receiving_yards',),
    'rec_td': ('receiving_tds',), 'rec_tgt': ('targets',), 'rec_2pt': (),
    'fum': ('fumbles',), 'fum_lost': ('fumbles_lost',),
    'pass_fd': ('passing_first_downs',), 'rush_fd': ('rushing_first_downs',),
    'rec_fd': ('receiving_first_downs',),
    'tkl_solo': ('tackles_solo',), 'tkl_ast': ('tackles_with_assist', 'tackles_assists'),
    'tkl_loss': ('tackles_for_loss',), 'sack': ('def_sacks', 'sacks'),
    'qb_hit': ('def_qb_hits', 'qb_hits'), 'int': ('def_interceptions',),
    'pass_def': ('def_pass_defended',), 'ff': ('def_fumbles_forced',),
    'fum_rec': ('def_fumbles',), 'def_td': ('def_tds',),
    'xpm': ('pat_made',), 'xpmiss': ('pat_missed',),
}


def finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError, OverflowError):
        return None


def audit_score(stats: dict, scoring: dict, position: str) -> dict:
    position = canonical_position(position)
    if not isinstance(stats, dict) or not isinstance(scoring, dict) or not scoring or not position:
        return {'status': 'BLOCKED_SCORING_INPUT', 'exact': False, 'points': None, 'keys': []}
    rows, total, relevant = [], 0.0, 0
    for key, raw_weight in sorted(scoring.items()):
        weight = finite(raw_weight)
        if weight is None:
            rows.append({'key': key, 'status': 'INVALID_WEIGHT'})
            continue
        if weight == 0:
            continue
        if not position_relevant(key, position):
            rows.append({'key': key, 'status': 'IRRELEVANT_POSITION'})
            continue
        relevant += 1
        if rule_spec(key) is None:
            rows.append({'key': key, 'status': 'UNKNOWN_SCORING_RULE'})
            continue
        if key in {'bonus_rec_te', 'rec_te'} and position == 'TE':
            names = ('rec', 'receptions')
        elif key in ALIASES:
            names = (key, *ALIASES[key])
        else:
            rows.append({'key': key, 'status': 'UNSUPPORTED_NONLINEAR_OR_EVENT_RULE'})
            continue
        present = [(name, finite(stats[name])) for name in names if name in stats]
        if not present:
            rows.append({'key': key, 'status': 'MISSING_RAW_STAT'})
        elif any(value is None for _, value in present):
            rows.append({'key': key, 'status': 'INVALID_RAW_STAT'})
        elif len({value for _, value in present}) > 1:
            rows.append({'key': key, 'status': 'CONFLICTING_RAW_ALIASES'})
        else:
            contribution = present[0][1] * weight
            if not math.isfinite(contribution):
                rows.append({'key': key, 'status': 'NONFINITE_CONTRIBUTION'})
                continue
            total += contribution
            rows.append({'key': key, 'status': 'EXACT_LINEAR', 'source_keys': [name for name, _ in present],
                         'stat_value': present[0][1], 'weight': weight, 'points': contribution})
    exact = relevant > 0 and math.isfinite(total) and all(row['status'] in {'EXACT_LINEAR', 'IRRELEVANT_POSITION'} for row in rows)
    return {'status': 'EXACT_LINEAR_BASELINE' if exact else 'BLOCKED_INCOMPLETE_BASELINE_SCORING',
            'exact': exact, 'points': round(total, 6) if exact else None,
            'position': position, 'relevant_keys': relevant, 'keys': rows}
