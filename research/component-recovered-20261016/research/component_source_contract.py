"""Explicit source bindings; source-native stats and provider parity are distinct."""
from __future__ import annotations

# Each tuple is an additive identity, not a list of interchangeable aliases.
PLAYER_FIELDS = {
    'passing_attempts': ('attempts',), 'passing_completions': ('completions',),
    'passing_yards': ('passing_yards',), 'passing_touchdowns': ('passing_tds',),
    'passing_interceptions': ('passing_interceptions',), 'passing_sacks_charged': ('sacks_suffered',),
    'passing_first_downs': ('passing_first_downs',),
    'passing_two_point_conversions': ('passing_2pt_conversions',),
    'rushing_attempts': ('carries',), 'rushing_yards': ('rushing_yards',),
    'rushing_touchdowns': ('rushing_tds',), 'rushing_first_downs': ('rushing_first_downs',),
    'rushing_two_point_conversions': ('rushing_2pt_conversions',),
    'receptions': ('receptions',), 'receiving_yards': ('receiving_yards',),
    'receiving_touchdowns': ('receiving_tds',), 'receiving_first_downs': ('receiving_first_downs',),
    'receiving_two_point_conversions': ('receiving_2pt_conversions',),
    'fumbles': ('fumbles_total',), 'fumbles_lost': ('fumbles_lost_total',),
    'kick_return_yards': ('kickoff_return_yards',), 'punt_return_yards': ('punt_return_yards',),
    'idp_tackles_solo': ('def_tackles_solo','def_tackles_with_assist'),
    'idp_tackles_assisted': ('def_tackle_assists',),
    'idp_tackles_total': ('def_tackles_solo', 'def_tackles_with_assist', 'def_tackle_assists'),
    'idp_tackles_for_loss': ('def_tackles_for_loss',), 'idp_sacks': ('def_sacks',),
    'idp_sack_yards': ('def_sack_yards',), 'idp_passes_defended': ('def_pass_defended',),
    'idp_interceptions': ('def_interceptions',), 'idp_interception_return_yards': ('def_interception_yards',),
    'idp_forced_fumbles': ('def_fumbles_forced',),
    'idp_fumble_recoveries': ('fumble_recovery_opp',),
    'idp_fumble_return_yards': ('fumble_recovery_yards_opp',),
    'idp_safeties': ('def_safeties',),
    'idp_blocked_kicks': ('def_punt_blocks', 'def_pat_blocks', 'def_fg_blocks'),
    'idp_defensive_touchdowns': ('def_tds',),
    'kicker_fgm': ('fg_made',), 'kicker_fgm_yds': ('fg_made_distance',),
    'kicker_fgmiss': ('fg_missed', 'fg_blocked'),
    'kicker_xpm': ('pat_made',), 'kicker_xpmiss': ('pat_missed', 'pat_blocked'),
    # Unscored opportunity/denominator components still belong to C1.
    'targets': ('targets',), 'passing_air_yards': ('passing_air_yards',),
    'receiving_air_yards': ('receiving_air_yards',),
    'receiving_yards_after_catch': ('receiving_yards_after_catch',),
    'kick_returns': ('kickoff_returns',), 'punt_returns': ('punt_returns',),
    'kicker_field_goal_attempts': ('fg_att',), 'kicker_extra_point_attempts': ('pat_att',),
    'kicker_blocked_field_goals': ('fg_blocked',), 'kicker_blocked_extra_points': ('pat_blocked',),
    'source_qb_hits_excluding_sacks': ('def_qb_hits',),
    'source_tackles_with_assist': ('def_tackles_with_assist',),
    'source_tackles_without_assist': ('def_tackles_solo',),
    'source_passing_first_downs_including_td': ('passing_first_downs',),
    'source_rushing_first_downs_including_td': ('rushing_first_downs',),
    'source_receiving_first_downs_including_td': ('receiving_first_downs',),
}
for band, suffix in [('0_19','0_19'), ('20_29','20_29'), ('30_39','30_39'),
                     ('40_49','40_49'), ('50_59','50_59'), ('60p','60_')]:
    PLAYER_FIELDS['kicker_fgm_' + band] = ('fg_made_' + suffix,)
PLAYER_FIELDS['kicker_fgm_50p'] = ('fg_made_50_59', 'fg_made_60_')

EVENT_FIELDS = {
    'passing_pick_sixes': 'event_pass_int_td',
    'offensive_fumble_recovery_touchdowns': 'event_fumble_recovery_tds',
    'individual_special_teams_touchdowns': 'event_special_teams_tds',
    'individual_special_teams_forced_fumbles': 'event_special_teams_forced_fumbles',
    'individual_special_teams_fumble_recoveries': 'event_special_teams_fumble_recoveries',
    'passing_completions_40_plus': 'event_pass_completions_40',
    'passing_touchdowns_40_plus': 'event_pass_tds_40',
    'passing_touchdowns_50_plus': 'event_pass_tds_50',
    'rushes_40_plus': 'event_rushes_40', 'rushing_touchdowns_40_plus': 'event_rush_tds_40',
    'rushing_touchdowns_50_plus': 'event_rush_tds_50',
    'receptions_40_plus': 'event_receptions_40',
    'receiving_touchdowns_40_plus': 'event_reception_tds_40',
    'receiving_touchdowns_50_plus': 'event_reception_tds_50',
}

# Sparse provider dictionaries: only an explicitly present key is observed.
# Omitted keys NEVER become zero. In particular, a team with gp=1 does not
# prove that every omitted rare stat is a published zero.
PROVIDER_OVERRIDES = {'idp_quarterback_hits': 'idp_qb_hit'}
DST_PLAYER_FIELDS = {
    'dst_sacks': ('def_sacks',), 'dst_interceptions': ('def_interceptions',),
    'dst_interception_return_yards': ('def_interception_yards',),
    'dst_defensive_touchdowns': ('def_tds',), 'dst_passes_defended': ('def_pass_defended',),
    'dst_kick_return_yards': ('kickoff_return_yards',), 'dst_punt_return_yards': ('punt_return_yards',),
    'dst_special_teams_touchdowns': ('special_teams_tds',),
}
POSITION_ALIASES = {
    'FB': 'RB', 'DE': 'DL', 'DT': 'DL', 'NT': 'DL', 'EDGE': 'DL', 'IDL': 'DL',
    'ILB': 'LB', 'OLB': 'LB', 'MLB': 'LB', 'CB': 'DB', 'S': 'DB', 'FS': 'DB',
    'SS': 'DB', 'SAF': 'DB', 'DST': 'DEF',
}
TEAM_ALIASES = {'JAC':'JAX', 'LA':'LAR', 'STL':'LAR', 'SD':'LAC', 'SDG':'LAC',
                'OAK':'LV', 'LVR':'LV', 'WSH':'WAS'}

def position(value):
    value = str(value).strip().upper()
    return POSITION_ALIASES.get(value, value)

def team(value):
    value = str(value).strip().upper()
    return TEAM_ALIASES.get(value, value)

SEMANTIC_SOURCES = {
    'options': 'https://support.sleeper.com/en/articles/3998131-what-scoring-options-are-available',
    'stacking': 'https://support.sleeper.com/en/articles/3186339-what-stacks',
    'special_teams': 'https://support.sleeper.com/en/articles/3278982-special-teams-scoring-options',
    'tackles': 'https://support.sleeper.com/en/articles/4056297-how-are-tackles-calculated',
    'points_allowed': 'https://support.sleeper.com/en/articles/4126495-how-are-points-allowed-calculated',
    'yards_allowed': 'https://support.sleeper.com/en/articles/4126427-how-are-yards-allowed-calculated',
    'nflverse': 'https://nflreadr.nflverse.com/articles/dictionary_player_stats.html',
    'nflverse_defense': 'https://nflreadr.nflverse.com/articles/dictionary_player_stats_def.html',
    'first_downs': 'https://sleeper.com/blog/point-per-first-down---an-alternative-to-ppr/',
}

def source_definition(component):
    if component in {'passing_first_downs','rushing_first_downs','receiving_first_downs'}:
        kind = component.removesuffix('_first_downs')
        return {'method':'PUBLISHED_FIRST_DOWNS_MINUS_TOUCHDOWNS','fields':[component,kind+'_tds'],
                'source_native_total_retained_separately':True,'provider_parity':'REQUIRES_MATCHED_PLAYER_WEEK_REPLAY'}
    if component in DST_PLAYER_FIELDS:
        return {'method':'ADDITIVE_PUBLISHED_TEAM_PLAYER_TOTALS','fields':list(DST_PLAYER_FIELDS[component]),
                'provider_parity':'REQUIRES_MATCHED_TEAM_WEEK_REPLAY'}
    if component in PLAYER_FIELDS:
        return {'method':'ADDITIVE_PUBLISHED_PLAYER_FIELDS', 'fields':list(PLAYER_FIELDS[component]),
                'provider_parity':'REQUIRES_MATCHED_PLAYER_WEEK_REPLAY'}
    if component in EVENT_FIELDS:
        return {'method':'SCOPED_CANONICAL_EVENT_LEDGER', 'fields':[EVENT_FIELDS[component]],
                'provider_parity':'REQUIRES_MATCHED_PLAYER_WEEK_REPLAY'}
    if component.startswith('prob_'):
        return {'method':'EXCLUSIVE_GAME_YARDAGE_BAND', 'provider_parity':'DOCUMENTED_SEMANTICS'}
    if component.startswith('dst_prob_pts_allow_'):
        return {'method':'EXCLUSIVE_PROVIDER_POINTS_ALLOWED_BAND',
                'provider_parity':'EXPLICIT_PROVIDER_STAT_ONLY'}
    return {'method':'EXPLICIT_PROVIDER_STAT_ONLY', 'provider_parity':'OMISSIONS_UNKNOWN',
            'reason':'No certified independent source derivation at C1; retain explicit provider outcomes only'}
