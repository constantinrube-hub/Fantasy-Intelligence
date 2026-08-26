# D/ST Integration Foundation

The separate D/ST research should plug into the 9.1 canonical contracts rather than creating a parallel feature stack.

## Do not add D/ST by

- creating another hard-coded position list;
- adding separate draft-replacement math;
- hand-parsing D/ST scoring in a feature module;
- duplicating lineup eligibility;
- creating a D/ST-only valuation score unrelated to League/Roster Value.

## Integration order

### 1. Extend scoring registry

Add/verify all team-DST Sleeper rule families in:

`config/contracts/runtime-contracts.json`

Regenerate JS/Python contracts.

### 2. D/ST entity identity

Represent team defenses with a canonical entity ID and `DEF` canonical position.

### 3. Projection distribution

D/ST research should produce expected weekly value plus uncertainty/tail values under exact league scoring.

### 4. Replacement

`ReplacementService` should automatically derive league D/ST replacement using roster slots, league size and available D/ST universe.

### 5. Lineup

`LineupOptimizer` already knows the DEF/DST slot contract. No separate D/ST lineup code should be required.

### 6. Decision services

D/ST then flows through:

```text
projection distribution
→ league value
→ roster marginal
→ draft/waiver/start-sit timing
```

### 7. Governance

Promote D/ST signals only after position-specific historical/forward validation clears the relevant decision domain.

## Required D/ST tests

- no D/ST rule affects offense-only leagues;
- every supported D/ST scoring key maps to a source/stat;
- team return rules are distinct from individual return rules;
- D/ST replacement scales by league size and roster count;
- bye/week availability is respected;
- start/sit matchup effects are temporally valid;
- no defensive opponent feature leaks same-week result information.
