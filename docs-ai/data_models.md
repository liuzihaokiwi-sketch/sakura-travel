# Data Models

## Layer A: Catalog (catalog.py) — 8 tables

| 表名 | 类名 | 关键字段 | 关系 |
|---|---|---|---|
| `entity_base` | `EntityBase` | entity_id(PK,UUID), entity_type, name_zh, name_ja, name_en, city_code, area_name, lat, lng, data_tier(S/A/B), google_place_id | → poi, hotel, restaurant, tags, media, editor_notes |
| `pois` | `Poi` | entity_id(PK,FK→entity_base), poi_category, typical_duration_min, admission_fee_jpy, best_season, google_rating | → entity |
| `hotels` | `Hotel` | entity_id(PK,FK→entity_base), hotel_type, star_rating, amenities(JSONB), price_tier, typical_price_min_jpy | → entity, area_guide |
| `restaurants` | `Restaurant` | entity_id(PK,FK→entity_base), cuisine_type, tabelog_score, michelin_star, requires_reservation, price_range_min/max_jpy | → entity |
| `entity_tags` | `EntityTag` | id(PK), entity_id(FK), tag_namespace, tag_value, source | → entity |
| `entity_media` | `EntityMedia` | id(PK), entity_id(FK), media_type, url, is_cover | → entity |
| `entity_editor_notes` | `EntityEditorNote` | id(PK), entity_id(FK), note_type, boost_value(-8~+8), content_zh | → entity |
| `hotel_area_guide` | `HotelAreaGuide` | id(PK), entity_id(FK→hotels), area_summary_zh, nearby_poi_ids(JSONB) | → hotel |

## Layer B: Snapshots (snapshots.py) — 6 tables

| 表名 | 类名 | 关键字段 |
|---|---|---|
| `source_snapshots` | `SourceSnapshot` | snapshot_id(PK), source_name, object_type, object_id, raw_payload(JSONB), fetched_at |
| `hotel_offer_snapshots` | `HotelOfferSnapshot` | offer_snapshot_id(PK), entity_id(FK), check_in_date, check_out_date, currency | → lines |
| `hotel_offer_lines` | `HotelOfferLine` | line_id(PK), offer_snapshot_id(FK), room_type, price_per_night, booking_url |
| `flight_offer_snapshots` | `FlightOfferSnapshot` | flight_snapshot_id(PK), origin_iata, dest_iata, departure_date, min_price |
| `poi_opening_snapshots` | `PoiOpeningSnapshot` | opening_snapshot_id(PK), entity_id(FK), check_date, is_open |
| `weather_snapshots` | `WeatherSnapshot` | weather_snapshot_id(PK), city_code, forecast_date, temp_high_c, condition |

## Layer C: Derived (derived.py) — 13 tables

| 表名 | 类名 | 关键字段 |
|---|---|---|
| `entity_scores` | `EntityScore` | score_id(PK), entity_id(FK), score_profile, base_score(0-100), editorial_boost(-8~+8), final_score |
| `itinerary_plans` | `ItineraryPlan` | plan_id(PK,UUID), trip_request_id(FK), version, status(draft/reviewed/published) | → days, scores |
| `itinerary_scores` | `ItineraryScore` | itinerary_score_id(PK), plan_id(FK), overall_score, diversity/efficiency/budget/preference scores |
| `planner_runs` | `PlannerRun` | planner_run_id(PK), trip_request_id(FK), status, algorithm_version |
| `candidate_sets` | `CandidateSet` | candidate_set_id(PK), planner_run_id(FK), city_code, entity_type, candidate_entity_ids(JSONB) |
| `route_matrix_cache` | `RouteMatrixCache` | cache_id(PK), origin_entity_id, dest_entity_id, travel_mode, duration_min |
| `itinerary_days` | `ItineraryDay` | day_id(PK), plan_id(FK), day_number, city_code, day_theme, hotel_entity_id(FK) | → items |
| `itinerary_items` | `ItineraryItem` | item_id(PK), day_id(FK), sort_order, item_type, entity_id(FK), start_time, duration_min |
| `route_templates` | `RouteTemplate` | template_id(PK,UUID), name_zh, city_code, duration_days, template_data(JSONB) |
| `render_templates` | `RenderTemplate` | render_template_id(PK), template_name, template_type, html_content |
| `export_jobs` | `ExportJob` | export_job_id(PK,UUID), plan_id(FK), export_type, status | → assets |
| `export_assets` | `ExportAsset` | asset_id(PK), export_job_id(FK), asset_type, storage_url |
| `plan_artifacts` | `PlanArtifact` | artifact_id(PK,UUID), plan_id(FK), order_id(FK), artifact_type, delivery_url, is_delivered |

## Layer D: Business (business.py) — 8 tables

| 表名 | 类名 | 关键字段 |
|---|---|---|
| `users` | `User` | user_id(PK,UUID), openid, phone, nickname | → orders |
| `product_sku` | `ProductSku` | sku_id(PK,str), sku_name, price_cny, sku_type, features(JSONB), max_days | → orders |
| `orders` | `Order` | order_id(PK,UUID), user_id(FK), sku_id(FK), status, amount_cny, payment_channel |
| `trip_requests` | `TripRequest` | trip_request_id(PK,UUID), user_id(FK), order_id(FK), raw_input(JSONB), status | → profile |
| `trip_profiles` | `TripProfile` | profile_id(PK,UUID), trip_request_id(FK,unique), cities(JSONB), duration_days, party_type, budget_level, must_have_tags(JSONB) |
| `trip_versions` | `TripVersion` | version_id(PK,UUID), trip_request_id(FK), plan_id(FK), version_number, change_reason |
| `review_jobs` | `ReviewJob` | review_job_id(PK,UUID), job_type, target_id, status, assigned_to, priority | → actions |
| `review_actions` | `ReviewAction` | action_id(PK), review_job_id(FK), action_type, actor, payload(JSONB) |