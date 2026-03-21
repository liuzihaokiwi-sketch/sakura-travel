## ADDED Requirements

### Requirement: Assembler SHALL validate commute times after assembly
After all slots are filled, the assembler SHALL iterate through each day's ordered entities and call `route_matrix.get_travel_time` for each adjacent pair. Any pair exceeding a 45-minute transit threshold SHALL be recorded as a warning.

#### Scenario: Adjacent entities within threshold
- **WHEN** two adjacent entities on the same day have a transit time of 30 minutes
- **THEN** no warning SHALL be generated for that pair

#### Scenario: Adjacent entities exceed threshold
- **WHEN** two adjacent entities (e.g., Asakusa → Odaiba) have a transit time of 55 minutes
- **THEN** a warning entry `{day, from_entity, to_entity, duration_min: 55}` SHALL be written to `plan_metadata.route_warnings`

#### Scenario: Route matrix API unavailable
- **WHEN** `get_travel_time` fails or returns None (API error, no cached data)
- **THEN** the assembler SHALL fall back to haversine distance estimation and log a warning, NOT block the assembly

### Requirement: Route warnings SHALL be stored in plan_metadata
The `plan_metadata` JSON column SHALL include a `route_warnings` array. Each entry SHALL contain `day` (int), `from_entity` (entity_id), `to_entity` (entity_id), and `duration_min` (int).

#### Scenario: Plan with no commute issues
- **WHEN** all adjacent pairs are within the 45-minute threshold
- **THEN** `plan_metadata.route_warnings` SHALL be an empty array `[]`

#### Scenario: Plan with multiple commute issues
- **WHEN** Day 2 has one pair at 50min and Day 3 has one pair at 60min
- **THEN** `plan_metadata.route_warnings` SHALL contain exactly 2 entries with the correct day numbers and durations
