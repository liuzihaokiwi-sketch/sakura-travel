## MODIFIED Requirements

### Requirement: Candidate sorting in planner.py
The planner's `_fetch_poi_candidates` and `_fetch_restaurant_candidates` functions SHALL JOIN with `EntityScore` and ORDER BY `EntityScore.final_score DESC` instead of the current `Poi.google_rating DESC` and `Restaurant.tabelog_score DESC`. This ensures both the old planner path and the new assembler path use the unified scoring engine for candidate ranking.

#### Scenario: POI candidates sorted by EntityScore
- **WHEN** the planner fetches POI candidates for a city with no template_code (old path)
- **THEN** candidates SHALL be ordered by `EntityScore.final_score DESC` instead of `Poi.google_rating DESC`

#### Scenario: Restaurant candidates sorted by EntityScore
- **WHEN** the planner fetches restaurant candidates for a meal slot
- **THEN** candidates SHALL be ordered by `EntityScore.final_score DESC` instead of `Restaurant.tabelog_score DESC`

#### Scenario: Entity has no EntityScore record
- **WHEN** an entity exists in the Poi/Restaurant table but has no corresponding EntityScore record
- **THEN** the entity SHALL still appear in candidates with a default score of 0, sorted to the bottom
