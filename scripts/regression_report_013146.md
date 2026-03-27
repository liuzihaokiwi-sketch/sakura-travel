# Travel AI Regression Report

- Generated at: 2026-03-27 01:31
- Case count: 1

## Coverage By Proof Level

- main_chain_proof: 1

## Assertions

- PASS: 4
- FAIL: 0

## phase2_kansai_family

- case_id: `phase2_kansai_family`
- description: Kansai family contract sample with do-not-go and booked hotel split.
- proof_level: `main_chain_proof`
- source_set: `phase2_contract_cases`
- entry_anchor: `normalize_trip_profile -> generate_trip._try_city_circle_pipeline`
- coverage_notes: phase2 contract-first case; should be counted as main-chain proof coverage
- day_count: 4
- cities: kyoto, osaka
- hotel_cities: kyoto, osaka

### Assertion Results

- [PASS] arrival_day_type: arrival
- [PASS] departure_day_type: departure
- [PASS] phase2:contract_fields_present: requested_city_circle
- [PASS] phase2:slot_lock_fixed_item_explicit_markers: count=2

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | osaka | Departure and wrap-up | departure
