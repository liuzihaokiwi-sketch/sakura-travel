#!/usr/bin/env python
"""
Final merge of Phase 1.5 discovery: ALL restaurants + hotels with deduplication.
Run this after all agents complete.
"""
import csv
from collections import defaultdict
from pathlib import Path

def merge_all_restaurants():
    """Merge all restaurant files (high-end + mid/budget + Tabelog + Trip/XHS)."""

    print("=" * 70)
    print("COMPREHENSIVE RESTAURANT MERGE (Phase 1.5 Final)")
    print("=" * 70)

    # Map of files to load, with schema hints
    input_files = {
        'restaurants_candidate_pool.csv': 'high_end',
        'restaurants_mid_budget_street.csv': 'mid_budget',
        'restaurants_mid_budget_candidates.csv': 'mid_budget',
        'restaurants_tabelog_by_cuisine.csv': 'tabelog_new',  # Will exist after agent
        'restaurants_trip_xhs_candidates.csv': 'trip_xhs_new',  # Will exist after agent
    }

    seen = {}  # key: (name_ja, city_code)
    source_mentions = defaultdict(list)

    total_loaded = 0
    for filename, file_type in input_files.items():
        filepath = Path(f'data/kansai_spots/{filename}')
        if not filepath.exists():
            print(f"[pending] {filename}")
            continue

        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if not row.get('name_ja') or row['name_ja'].startswith('#'):
                    continue

                key = (row['name_ja'], row['city_code'])
                if key not in seen:
                    # Normalize schema
                    normalized = {
                        'name_ja': row['name_ja'],
                        'city_code': row['city_code'],
                        'area': row.get('area', ''),
                        'cuisine_type': row.get('cuisine_type') or row.get('cuisine', ''),
                        'budget_tier': row.get('budget_tier', 'mid'),
                        'tabelog_score': row.get('tabelog_score', ''),
                        'michelin': row.get('michelin', ''),
                        'source': row.get('source_url') or row.get('source', ''),
                        'notes': row.get('brief_note') or row.get('notes', row.get('extra_info', ''))
                    }
                    seen[key] = normalized
                    source_mentions[key].append(filename)
                    count += 1
                else:
                    # Multi-source mention
                    source_mentions[key].append(filename)

            total_loaded += count
            print(f"[ok] {filename:45} (+{count:3} unique)")

    print(f"\n[summary] Total unique restaurants: {len(seen)}")

    # Analysis by city
    cities = defaultdict(int)
    budgets = defaultdict(int)
    for (name, city), row in seen.items():
        cities[city] += 1
        budgets[row['budget_tier']] += 1

    print("\n[city-distribution]")
    for city in sorted(cities.keys()):
        print(f"  {city:15} {cities[city]:3} entries")

    print("\n[budget-distribution]")
    for tier in ['luxury', 'expensive', 'mid', 'budget', 'street', 'unknown']:
        if budgets[tier] > 0:
            pct = budgets[tier] / len(seen) * 100
            print(f"  {tier:10} {budgets[tier]:3} entries ({pct:5.1f}%)")

    # Multi-source analysis
    multi_source_count = sum(1 for mentions in source_mentions.values() if len(mentions) > 1)
    print(f"\n[confidence] {multi_source_count} restaurants mentioned in 2+ sources")

    # Write output
    output_file = 'data/kansai_spots/restaurants_merged_final.csv'
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['name_ja', 'city_code', 'area', 'cuisine_type', 'budget_tier',
                     'tabelog_score', 'michelin', 'source', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (name, city), row in sorted(seen.items()):
            writer.writerow(row)

    print(f"\n[output] {output_file}")

    # Target assessment
    target_min, target_max = 700, 800
    pct = len(seen) / ((target_min + target_max) / 2) * 100
    status = "ON_TRACK" if pct >= 60 else "NEEDS_MORE"
    print(f"[target] {len(seen)} / {target_min}-{target_max} ({pct:.0f}%) [{status}]")

    return seen


def merge_all_hotels():
    """Merge all hotel files (high-end + mid/budget + onsen/small cities)."""

    print("\n" + "=" * 70)
    print("COMPREHENSIVE HOTEL MERGE (Phase 1.5 Final)")
    print("=" * 70)

    input_files = {
        'hotels_candidate_pool.csv': 'high_end',
        'hotels_mid_budget_candidates.csv': 'mid_budget_1',
        'hotels_midrange_budget_candidates.csv': 'mid_budget_2',
        'hotels_onsen_area_candidates.csv': 'onsen_new',  # Will exist after agent
    }

    seen = {}  # key: (name_ja, city_code)
    source_mentions = defaultdict(list)

    total_loaded = 0
    for filename, file_type in input_files.items():
        filepath = Path(f'data/kansai_spots/{filename}')
        if not filepath.exists():
            print(f"[pending] {filename}")
            continue

        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if not row.get('name_ja') or row['name_ja'].startswith('#'):
                    continue

                key = (row['name_ja'], row['city_code'])
                if key not in seen:
                    normalized = {
                        'name_ja': row['name_ja'],
                        'city_code': row['city_code'],
                        'area': row.get('area', ''),
                        'hotel_type': row.get('hotel_type', ''),
                        'price_level': row.get('price_level', 'moderate'),
                        'key_features': row.get('key_features', row.get('key_feature', '')),
                        'source': row.get('source_url') or row.get('source', ''),
                        'notes': row.get('brief_note') or row.get('notes', '')
                    }
                    seen[key] = normalized
                    source_mentions[key].append(filename)
                    count += 1
                else:
                    source_mentions[key].append(filename)

            total_loaded += count
            print(f"[ok] {filename:45} (+{count:3} unique)")

    print(f"\n[summary] Total unique hotels: {len(seen)}")

    # Analysis by city
    cities = defaultdict(int)
    prices = defaultdict(int)
    for (name, city), row in seen.items():
        cities[city] += 1
        prices[row['price_level']] += 1

    print("\n[city-distribution]")
    for city in sorted(cities.keys()):
        print(f"  {city:15} {cities[city]:3} entries")

    print("\n[price-distribution]")
    for level in ['luxury', 'expensive', 'moderate', 'budget', 'backpacker']:
        if prices[level] > 0:
            pct = prices[level] / len(seen) * 100
            print(f"  {level:12} {prices[level]:3} entries ({pct:5.1f}%)")

    # Multi-source analysis
    multi_source_count = sum(1 for mentions in source_mentions.values() if len(mentions) > 1)
    print(f"\n[confidence] {multi_source_count} hotels mentioned in 2+ sources")

    # Write output
    output_file = 'data/kansai_spots/hotels_merged_final.csv'
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['name_ja', 'city_code', 'area', 'hotel_type', 'price_level',
                     'key_features', 'source', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (name, city), row in sorted(seen.items()):
            writer.writerow(row)

    print(f"\n[output] {output_file}")

    # Target assessment
    target_min, target_max = 500, 600
    pct = len(seen) / ((target_min + target_max) / 2) * 100
    status = "ON_TRACK" if pct >= 60 else "NEEDS_MORE"
    print(f"[target] {len(seen)} / {target_min}-{target_max} ({pct:.0f}%) [{status}]")

    return seen


def final_assessment(restaurants, hotels):
    """Assess overall readiness for Phase 2."""

    print("\n" + "=" * 70)
    print("PHASE 1.5 FINAL ASSESSMENT")
    print("=" * 70)

    rest_pct = len(restaurants) / 750 * 100  # 750 = average of 700-800
    hotel_pct = len(hotels) / 550 * 100  # 550 = average of 500-600

    print(f"\nRestaurants: {len(restaurants):3} / ~750 target ({rest_pct:5.1f}%)")
    print(f"Hotels:      {len(hotels):3} / ~550 target ({hotel_pct:5.1f}%)")

    print("\n[recommendation]")
    if rest_pct >= 70 and hotel_pct >= 70:
        print("  PROCEED TO PHASE 2 (sufficient discovery pool)")
    elif rest_pct >= 60 and hotel_pct >= 60:
        print("  PROCEED WITH CAUTION (tight but viable)")
    else:
        print("  RECOMMEND 1 MORE ROUND before Phase 2")
        print("    - Tabelog: remaining cuisines not yet covered")
        print("    - Retty/GURUNAVI: alternative restaurant sources")
        print("    - Booking.com: alternative hotel sources")


if __name__ == '__main__':
    restaurants = merge_all_restaurants()
    hotels = merge_all_hotels()
    final_assessment(restaurants, hotels)
    print("\n[done]")
