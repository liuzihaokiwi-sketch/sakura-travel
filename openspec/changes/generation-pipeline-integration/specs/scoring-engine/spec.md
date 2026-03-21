## MODIFIED Requirements

### Requirement: Assembler SHALL invoke compute_candidate_score with user_weights
The assembler's candidate selection SHALL call `compute_candidate_score` from `scorer.py`, passing `user_weights` constructed from `TripProfile.party_type` and tag preferences, along with `entity_affinity` tags for each candidate. This replaces the current usage of raw `EntityScore.final_score` as the sole sort key.

The `compute_candidate_score` function already supports a 3D formula:
```
candidate_score = w_sys × system_score + w_ctx × context_score + w_soft × soft_rule_score - risk_penalty
```

The assembler SHALL provide the runtime `user_weights` that drive `w_ctx` and `w_soft` weighting.

#### Scenario: Assembler provides user_weights from TripProfile
- **WHEN** the assembler builds candidates for a trip with `party_type = "family"`
- **THEN** `user_weights` SHALL be constructed from `SEGMENT_PACK_SEEDS["family_child"]` merged with `stage_weight_pack("standard")`

#### Scenario: Candidate scoring uses 3D formula when soft scores exist
- **WHEN** an entity has entries in `entity_soft_scores` for the 12 soft-rule dimensions
- **THEN** `compute_candidate_score` SHALL use the full 3D formula including the soft_rule_score component

#### Scenario: Candidate scoring falls back to 2D when soft scores missing
- **WHEN** an entity has no `entity_soft_scores` entry
- **THEN** `compute_candidate_score` SHALL use the 2D formula (system_score + context_score) with `soft_rule_score = None`

### Requirement: context_score status update
The `context_score` component referenced in the scoring engine spec as "❌ 未实现" is now partially addressed through user_weights integration. The assembler SHALL pass user tag preferences as the basis for context scoring within `compute_candidate_score`. Full standalone `context_score` computation remains a future enhancement.

#### Scenario: User tags influence context scoring
- **WHEN** TripProfile has `must_have_tags = ["温泉", "美食"]`
- **THEN** entities with high affinity on "温泉" and "美食" tags SHALL receive higher context-weighted scores
