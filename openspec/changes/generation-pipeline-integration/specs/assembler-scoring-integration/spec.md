## ADDED Requirements

### Requirement: Assembler SHALL use 3D candidate scoring
The assembler's `fetch_slot_candidates` function SHALL score each candidate using `compute_candidate_score` from `scorer.py`, passing in user_weights derived from the trip profile and entity_affinity tags. The resulting `final_score` SHALL replace the raw `EntityScore.final_score` as the sort key for candidate ranking.

#### Scenario: Family trip selects relaxation-friendly entities
- **WHEN** TripProfile.party_type is "family" and assembler fetches candidates for a sightseeing slot
- **THEN** candidates with higher soft_rule scores on dimensions like "relaxation" and "体力友好度" SHALL rank higher than candidates with only high system scores

#### Scenario: Soft rule scores unavailable gracefully degrades to 2D
- **WHEN** a candidate entity has no entry in entity_soft_scores
- **THEN** the scorer SHALL fall back to the 2D formula (system_score + context_score) without error, using default weight pack values

#### Scenario: Couple trip prioritises shareability
- **WHEN** TripProfile.party_type is "couple" and assembler fetches candidates
- **THEN** the couple segment weight pack SHALL boost "可拍性" and "情绪价值" dimensions, resulting in photogenic / romantic entities ranking higher

### Requirement: User weights SHALL be derived from TripProfile
The assembler SHALL construct `user_weights` by mapping `TripProfile.party_type` to the corresponding segment pack in `SEGMENT_PACK_SEEDS`, then merging with `stage_weight_pack("standard")`. `must_have_tags` and `nice_to_have_tags` from TripProfile SHALL also influence the user_weights dictionary.

#### Scenario: Solo traveller mapping
- **WHEN** TripProfile.party_type is "solo"
- **THEN** user_weights SHALL be built from the `first_time_fit` segment pack merged with the `standard` stage weight pack

#### Scenario: Parents mapping
- **WHEN** TripProfile.party_type is "parents"
- **THEN** user_weights SHALL be built from the `parents` segment pack

#### Scenario: Must-have tags boost
- **WHEN** TripProfile.must_have_tags includes "温泉"
- **THEN** entities tagged with "温泉" SHALL receive a boosted affinity score in the candidate scoring
