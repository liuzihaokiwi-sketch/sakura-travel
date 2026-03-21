## ADDED Requirements

### Requirement: Generate-trip job SHALL mark the best preview day
After assembly and copywriting enrichment, the `generate_trip` job SHALL call `select_preview_day` from `preview_engine.py` to determine which day is best suited for the customer preview. The result SHALL be stored in `plan_metadata.preview_day`.

#### Scenario: Normal multi-day itinerary
- **WHEN** a 5-day itinerary is generated with day scores varying across days
- **THEN** `plan_metadata.preview_day` SHALL be set to the day index with the highest composite preview score (typically not the arrival or departure day)

#### Scenario: Preview engine flags uncertainty
- **WHEN** `select_preview_day` returns `needs_human_review = true` (e.g., multiple days tied or all scores low)
- **THEN** `plan_metadata.preview_needs_review` SHALL be set to `true` and `plan_metadata.preview_day` SHALL still contain the engine's best guess

#### Scenario: Short itinerary (2 days)
- **WHEN** a 2-day itinerary has only arrival day and departure day
- **THEN** `select_preview_day` SHALL pick the day with more substantive content and `plan_metadata.preview_needs_review` SHALL be `true`

### Requirement: Preview day data format
The itinerary day data SHALL be converted to the `list[list[dict]]` format required by `select_preview_day` before invocation. Each inner list represents one day, each dict represents one entity with keys including `entity_id`, `entity_type`, `name`, `tags`, and `copy_text`.

#### Scenario: Data conversion preserves entity order
- **WHEN** Day 3 has entities [A, B, C] in slot order
- **THEN** the converted data for Day 3 SHALL be `[{entity A}, {entity B}, {entity C}]` in the same order
