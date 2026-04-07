#!/usr/bin/env python
"""
Merge restaurant and hotel candidates from multiple sources with deduplication.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

def deduplicate_restaurants(output_file='data/kansai_spots/restaurants_merged.csv'):
    """Merge all restaurant candidate CSVs with deduplication by (name_ja, city_code)."""

    restaurant_files = [
        'data/kansai_spots/restaurants_candidate_pool.csv',
        'data/kansai_spots/restaurants_mid_budget_street.csv',
        'data/kansai_spots/restaurants_mid_budget_candidates.csv',
        'data/kansai_spots/restaurants_tabelog_by_cuisine.csv',  # Will exist after agent completes
        'data/kansai_spots/restaurants_trip_xhs_candidates.csv',  # Will exist after agent completes
    ]

    seen = {}  # key: (name_ja, city_code), value: row dict
    source_log = defaultdict(list)

    for filepath in restaurant_files:
        path = Path(filepath)
        if not path.exists():
            print(f"[pending] {filepath} not yet available")
            continue

        print(f"[reading] {path.name}...")
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip comment rows
                if not row.get('name_ja') or row['name_ja'].startswith('#'):
                    continue

                key = (row['name_ja'], row['city_code'])
                if key not in seen:
                    seen[key] = row
                    source_log[key] = [path.name]
                else:
                    # Log which sources mention this restaurant
                    source_log[key].append(path.name)

    print(f"\n[OK] Merged into {len(seen)} unique restaurants")

    # Breakdown by city
    cities = defaultdict(int)
    for (name, city), row in seen.items():
        cities[city] += 1

    print("\n[city-distribution] City breakdown:")
    for city in sorted(cities.keys()):
        print(f"  {city}: {cities[city]}")

    # Breakdown by budget tier (if available)
    budgets = defaultdict(int)
    for row in seen.values():
        if 'budget_tier' in row:
            budgets[row['budget_tier']] += 1

    if budgets:
        print("\n[budget-distribution] Budget breakdown:")
        for tier in sorted(budgets.keys()):
            print(f"  {tier}: {budgets[tier]}")

    # Write merged file
    if seen:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Get fieldnames from the first row
            first_row = next(iter(seen.values()))
            fieldnames = list(first_row.keys())

            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for (name, city), row in sorted(seen.items()):
                writer.writerow(row)

        print(f"\n[file] Merged file written to: {output_file}")

    # Summary statistics
    multi_source = sum(1 for sources in source_log.values() if len(sources) > 1)
    print(f"\n[sources] Multi-source mentions: {multi_source} restaurants")

    return seen


def deduplicate_hotels(output_file='data/kansai_spots/hotels_merged.csv'):
    """Merge all hotel candidate CSVs with deduplication by (name_ja, city_code)."""

    hotel_files = [
        'data/kansai_spots/hotels_candidate_pool.csv',
        'data/kansai_spots/hotels_mid_budget_candidates.csv',
        'data/kansai_spots/hotels_midrange_budget_candidates.csv',
        'data/kansai_spots/hotels_onsen_area_candidates.csv',  # Will exist after agent completes
    ]

    seen = {}  # key: (name_ja, city_code), value: row dict
    source_log = defaultdict(list)

    for filepath in hotel_files:
        path = Path(filepath)
        if not path.exists():
            print(f"[pending] {filepath} not yet available")
            continue

        print(f"[reading] {path.name}...")
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('name_ja') or row['name_ja'].startswith('#'):
                    continue

                key = (row['name_ja'], row['city_code'])
                if key not in seen:
                    seen[key] = row
                    source_log[key] = [path.name]
                else:
                    source_log[key].append(path.name)

    print(f"\n[OK] Merged into {len(seen)} unique hotels")

    # Breakdown by city
    cities = defaultdict(int)
    for (name, city), row in seen.items():
        cities[city] += 1

    print("\n[city-distribution] City breakdown:")
    for city in sorted(cities.keys()):
        print(f"  {city}: {cities[city]}")

    # Breakdown by price level (if available)
    prices = defaultdict(int)
    for row in seen.values():
        if 'price_level' in row:
            prices[row['price_level']] += 1

    if prices:
        print("\n[price-distribution] Price breakdown:")
        for level in ['luxury', 'expensive', 'moderate', 'budget', 'backpacker']:
            if level in prices:
                print(f"  {level}: {prices[level]}")

    # Write merged file
    if seen:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Get fieldnames from the first row
            first_row = next(iter(seen.values()))
            fieldnames = list(first_row.keys())

            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for (name, city), row in sorted(seen.items()):
                writer.writerow(row)

        print(f"\n[file] Merged file written to: {output_file}")

    # Summary statistics
    multi_source = sum(1 for sources in source_log.values() if len(sources) > 1)
    print(f"\n[sources] Multi-source mentions: {multi_source} hotels")

    return seen


if __name__ == '__main__':
    print("=" * 60)
    print("RESTAURANT MERGER")
    print("=" * 60)
    restaurants = deduplicate_restaurants()

    print("\n" + "=" * 60)
    print("HOTEL MERGER")
    print("=" * 60)
    hotels = deduplicate_hotels()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total restaurants (merged): {len(restaurants)}")
    print(f"Total hotels (merged): {len(hotels)}")
    print("\nTarget: ~700-800 restaurants, ~500-600 hotels")
    print("\nStatus:")
    rest_pct = len(restaurants) / 750 * 100 if restaurants else 0
    hotel_pct = len(hotels) / 550 * 100 if hotels else 0
    print(f"  Restaurants: {len(restaurants)} ({rest_pct:.0f}% of target)")
    print(f"  Hotels: {len(hotels)} ({hotel_pct:.0f}% of target)")

    if len(restaurants) < 700:
        print("\n[warn] Restaurants still below target. Waiting for agent outputs...")
    if len(hotels) < 500:
        print("\n[warn] Hotels still below target. Waiting for agent outputs...")
