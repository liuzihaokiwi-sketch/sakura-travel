# Travel AI Regression Report

- Generated at: 2026-03-27 02:53
- Case count: 15

## Coverage By Proof Level

- compatibility_baseline: 10
- main_chain_proof: 5

## Assertions

- PASS: 52
- FAIL: 0

## 标准型 · 情侣首次关西

- case_id: `standard`
- description: 最常见用户画像，验证主链路是否稳定输出
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 6
- cities: kyoto, osaka
- hotel_cities: kyoto, osaka

### Assertion Results

- [PASS] days>=6: actual=6
- [PASS] days<=6: actual=6
- [PASS] arrival_day_type: arrival
- [PASS] departure_day_type: departure
- [PASS] departure_day_no_poi: items=0

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | osaka | City exploration | sightseeing
- Day 5 | kyoto | City exploration | sightseeing
- Day 6 | osaka | Departure and wrap-up | departure

## 约束型 · 三代同堂家庭 [BLOCKER]

- case_id: `constrained`
- description: 大量限制条件，验证规则引擎和约束传递是否生效
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 5
- cities: kyoto, osaka
- hotel_cities: kyoto, osaka

### Assertion Results

- [PASS] days>=5: actual=5
- [PASS] days<=5: actual=5
- [PASS] departure_day_type: departure

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | osaka | City exploration | sightseeing
- Day 5 | kyoto | Departure and wrap-up | departure

## 边界型 · 单人穷游短行程

- case_id: `edge`
- description: 到达晚、预算紧、天数少但想去的多，验证 fallback 和特殊 day type
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 4
- cities: osaka
- hotel_cities: osaka

### Assertion Results

- [PASS] days>=4: actual=4
- [PASS] days<=4: actual=4
- [PASS] arrival_day_type: arrival
- [PASS] departure_day_type: departure

### Itinerary Summary

- Day 1 | osaka | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | osaka | City exploration | sightseeing
- Day 4 | osaka | Departure and wrap-up | departure

## 季节型 · 闺蜜樱花季摄影

- case_id: `sakura`
- description: 樱花季高峰出行，验证季节性权重、花期时间窗和预约压力
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 7
- cities: kyoto, osaka
- hotel_cities: kyoto, osaka

### Assertion Results

- [PASS] days>=7: actual=7
- [PASS] days<=7: actual=7
- [PASS] arrival_day_type: arrival
- [PASS] departure_day_type: departure

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | osaka | City exploration | sightseeing
- Day 5 | kyoto | City exploration | sightseeing
- Day 6 | osaka | City exploration | sightseeing
- Day 7 | kyoto | Departure and wrap-up | departure

## 小众型 · 建筑师深度庭园线

- case_id: `niche`
- description: 冷门兴趣+饮食限制+拒绝热门景点，验证长尾覆盖和约束叠加
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 5
- cities: kyoto
- hotel_cities: kyoto

### Assertion Results

- [PASS] days>=5: actual=5
- [PASS] days<=5: actual=5
- [PASS] departure_day_type: departure

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | kyoto | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | kyoto | City exploration | sightseeing
- Day 5 | kyoto | Departure and wrap-up | departure

## 约束型 · 明确拒绝景点

- case_id: `must_not_go`
- description: 用户明确 blocked_clusters，验证拒绝项不出现在行程中
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 5
- cities: kyoto, osaka
- hotel_cities: kyoto, osaka

### Assertion Results

- [PASS] days>=5: actual=5
- [PASS] days<=5: actual=5

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | osaka | City exploration | sightseeing
- Day 5 | kyoto | Departure and wrap-up | departure

## 约束型 · 纯餐饮禁忌

- case_id: `avoid_cuisine`
- description: 多种餐饮禁忌叠加，验证 avoid_cuisines 贯穿
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 4
- cities: osaka
- hotel_cities: osaka

### Assertion Results

- [PASS] days>=4: actual=4
- [PASS] days<=4: actual=4

### Itinerary Summary

- Day 1 | osaka | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | osaka | City exploration | sightseeing
- Day 4 | osaka | Departure and wrap-up | departure

## 边界型 · 返程直奔机场

- case_id: `airport_return`
- description: departure_day_shape=direct_to_airport，验证返程日无 POI
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 4
- cities: kyoto, osaka
- hotel_cities: kyoto, osaka

### Assertion Results

- [PASS] days>=4: actual=4
- [PASS] days<=4: actual=4
- [PASS] departure_day_type: departure
- [PASS] departure_day_no_poi: items=0

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | osaka | Departure and wrap-up | departure

## 标准型 · USJ 主题公园

- case_id: `theme_park`
- description: 必含 USJ 独立成天，验证 theme_park day 结构
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 5
- cities: osaka, kyoto
- hotel_cities: osaka, kyoto

### Assertion Results

- [PASS] days>=5: actual=5
- [PASS] days<=5: actual=5

### Itinerary Summary

- Day 1 | osaka | Arrival and light settle-in | arrival
- Day 2 | kyoto | City exploration | sightseeing
- Day 3 | osaka | City exploration | sightseeing
- Day 4 | kyoto | City exploration | sightseeing
- Day 5 | osaka | Departure and wrap-up | departure

## 约束型 · 老年低强度

- case_id: `elderly_low`
- description: senior + relaxed，验证 max_intensity 全天不超过 light
- proof_level: `compatibility_baseline`
- source_set: `legacy_profile_cases`
- entry_anchor: `run_regression direct profile assembly path`
- coverage_notes: legacy-profile regression case; should be counted as compatibility baseline coverage
- day_count: 5
- cities: kyoto
- hotel_cities: kyoto

### Assertion Results

- [PASS] days>=5: actual=5
- [PASS] days<=5: actual=5
- [PASS] departure_day_type: departure

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | kyoto | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | kyoto | City exploration | sightseeing
- Day 5 | kyoto | Departure and wrap-up | departure

## phase2_migrated_contract

- case_id: `phase2_migrated_contract`
- description: Single migrated contract sample for Phase 2 entry migration.
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
- [PASS] phase2:slot_lock_fixed_item_explicit_markers: count=1

### Itinerary Summary

- Day 1 | kyoto | Arrival and light settle-in | arrival
- Day 2 | osaka | City exploration | sightseeing
- Day 3 | kyoto | City exploration | sightseeing
- Day 4 | osaka | Departure and wrap-up | departure

## phase2_kanto_booked

- case_id: `phase2_kanto_booked`
- description: Kanto city circle contract sample with booked hotel and fixed item.
- proof_level: `main_chain_proof`
- source_set: `phase2_contract_cases`
- entry_anchor: `normalize_trip_profile -> generate_trip._try_city_circle_pipeline`
- coverage_notes: phase2 contract-first case; should be counted as main-chain proof coverage
- day_count: 4
- cities: tokyo, yokohama
- hotel_cities: tokyo, yokohama

### Assertion Results

- [PASS] arrival_day_type: arrival
- [PASS] departure_day_type: departure
- [PASS] phase2:contract_fields_present: requested_city_circle
- [PASS] phase2:slot_lock_fixed_item_explicit_markers: count=2

### Itinerary Summary

- Day 1 | tokyo | Arrival and light settle-in | arrival
- Day 2 | yokohama | City exploration | sightseeing
- Day 3 | tokyo | City exploration | sightseeing
- Day 4 | yokohama | Departure and wrap-up | departure

## phase2_hokkaido

- case_id: `phase2_hokkaido`
- description: Hokkaido circle contract sample with arrival/departure strict semantics.
- proof_level: `main_chain_proof`
- source_set: `phase2_contract_cases`
- entry_anchor: `normalize_trip_profile -> generate_trip._try_city_circle_pipeline`
- coverage_notes: phase2 contract-first case; should be counted as main-chain proof coverage
- day_count: 3
- cities: sapporo
- hotel_cities: sapporo

### Assertion Results

- [PASS] arrival_day_type: arrival
- [PASS] departure_day_type: departure
- [PASS] phase2:contract_fields_present: requested_city_circle
- [PASS] phase2:slot_lock_fixed_item_explicit_markers: count=1

### Itinerary Summary

- Day 1 | sapporo | Arrival and light settle-in | arrival
- Day 2 | sapporo | City exploration | sightseeing
- Day 3 | sapporo | Departure and wrap-up | departure

## phase2_south_china

- case_id: `phase2_south_china`
- description: South China five-city circle sample with fixed item lock.
- proof_level: `main_chain_proof`
- source_set: `phase2_contract_cases`
- entry_anchor: `normalize_trip_profile -> generate_trip._try_city_circle_pipeline`
- coverage_notes: phase2 contract-first case; should be counted as main-chain proof coverage
- day_count: 4
- cities: guangzhou, shenzhen
- hotel_cities: guangzhou, shenzhen

### Assertion Results

- [PASS] arrival_day_type: arrival
- [PASS] departure_day_type: departure
- [PASS] phase2:contract_fields_present: requested_city_circle
- [PASS] phase2:slot_lock_fixed_item_explicit_markers: count=1

### Itinerary Summary

- Day 1 | guangzhou | Arrival and light settle-in | arrival
- Day 2 | shenzhen | City exploration | sightseeing
- Day 3 | guangzhou | City exploration | sightseeing
- Day 4 | shenzhen | Departure and wrap-up | departure

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
