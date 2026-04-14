## ADDED Requirements

### Requirement: Guardrails SHALL run full 6-item check per day
The `run_guardrails` job SHALL invoke `swap_safety.check_single_day_guardrails` for each itinerary day, covering all 6 hard/soft checks: closing day conflicts, overloaded days (暴走), missing meals, duplicate entities, time overlap, and opening hours violations.

#### Scenario: Day with closing-day conflict
- **WHEN** an entity's known closing day (定休日) matches the itinerary day's weekday
- **THEN** guardrails SHALL report a hard_fail for that entity on that day

#### Scenario: Overloaded day (too many walking-heavy POIs)
- **WHEN** a single day has more than 5 sightseeing POIs requiring significant walking
- **THEN** guardrails SHALL report a soft_fail warning for 暴走 risk on that day

#### Scenario: Day missing lunch slot
- **WHEN** a day has no restaurant entity scheduled between 11:00-14:00
- **THEN** guardrails SHALL report a soft_fail warning for missing meal

#### Scenario: Duplicate entity in same plan
- **WHEN** the same entity_id appears more than once across all days
- **THEN** guardrails SHALL report a hard_fail for the duplicate

### Requirement: Guardrail warnings SHALL be stored in plan_metadata
Soft-fail items from guardrail checks SHALL be written to `plan_metadata.guardrail_warnings` as an array. Hard-fail items SHALL be aggregated into the errors list that blocks plan approval.

#### Scenario: Plan passes all guardrails
- **WHEN** no hard_fail or soft_fail items are found
- **THEN** `plan_metadata.guardrail_warnings` SHALL be an empty array and no errors SHALL be raised

#### Scenario: Plan has soft warnings only
- **WHEN** guardrails find 2 soft_fail items but no hard_fail items
- **THEN** the plan SHALL NOT be blocked, and `plan_metadata.guardrail_warnings` SHALL contain 2 entries

### Requirement: Existing MIN_ITEMS and MAX_DUPLICATE checks SHALL be preserved
The current basic guardrail checks (minimum items per day and maximum duplicate ratio) SHALL remain as additional rules alongside the new `check_single_day_guardrails` integration.

#### Scenario: Day with too few items
- **WHEN** a day has fewer than the configured MIN_ITEMS threshold
- **THEN** guardrails SHALL report an error regardless of `check_single_day_guardrails` output
