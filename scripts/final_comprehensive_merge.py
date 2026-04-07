#!/usr/bin/env python
"""
FINAL comprehensive merge after ALL Phase 1.5 agents complete.
Run this once Tabelog agent finishes.
"""
import csv
from collections import defaultdict
from pathlib import Path

def merge_all():
    print("=" * 80)
    print("PHASE 1.5 FINAL COMPREHENSIVE MERGE")
    print("=" * 80)

    # Restaurants: 5 sources (high-end, 2x mid/budget, Trip/XHS, Tabelog)
    restaurant_files = [
        'data/kansai_spots/restaurants_candidate_pool.csv',
        'data/kansai_spots/restaurants_mid_budget_street.csv',
        'data/kansai_spots/restaurants_mid_budget_candidates.csv',
        'data/kansai_spots/restaurants_trip_xhs_candidates.csv',
        'data/kansai_spots/restaurants_tabelog_by_cuisine.csv',
    ]

    rest_seen = {}
    rest_sources = defaultdict(list)
    rest_stats = defaultdict(int)

    print("\n[RESTAURANTS]")
    for filepath in restaurant_files:
        path = Path(filepath)
        if not path.exists():
            print(f"  [pending] {path.name}")
            continue

        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if not row.get('name_ja') or row['name_ja'].startswith('#'):
                    continue

                key = (row['name_ja'], row['city_code'])
                if key not in rest_seen:
                    # Normalize schema
                    budget = row.get('budget_tier')
                    if not budget and filepath.endswith('candidate_pool.csv'):
                        budget = 'luxury'
                    elif not budget:
                        budget = 'mid'

                    rest_seen[key] = {
                        'name_ja': row['name_ja'],
                        'city_code': row['city_code'],
                        'area': row.get('area', ''),
                        'cuisine_type': row.get('cuisine_type', row.get('cuisine', '')),
                        'budget_tier': budget,
                        'tabelog_score': row.get('tabelog_score', ''),
                        'michelin': row.get('michelin', ''),
                        'mention_count': row.get('mention_count', ''),
                        'source': row.get('source_url', row.get('source', '')),
                    }
                    rest_sources[key].append(path.name)
                    count += 1
                else:
                    rest_sources[key].append(path.name)

            rest_stats[path.name] = count
            print(f"  [ok] {path.name:45} (+{count:3})")

    print(f"\n  TOTAL: {len(rest_seen)} unique restaurants")

    # Budget distribution
    budgets = defaultdict(int)
    cities = defaultdict(int)
    for (name, city), row in rest_seen.items():
        budgets[row['budget_tier']] += 1
        cities[city] += 1

    print("\n  [Budget distribution]")
    for tier in ['luxury', 'expensive', 'mid', 'budget', 'street']:
        count = budgets[tier]
        if count > 0:
            pct = count / len(rest_seen) * 100
            print(f"    {tier:10} {count:3} ({pct:5.1f}%)")

    # Multi-source
    multi_src = sum(1 for sources in rest_sources.values() if len(sources) > 1)
    print(f"\n  [Confidence] {multi_src} restaurants from 2+ sources ({multi_src/len(rest_seen)*100:.1f}%)")

    # Hotels: 4 sources
    hotel_files = [
        'data/kansai_spots/hotels_candidate_pool.csv',
        'data/kansai_spots/hotels_mid_budget_candidates.csv',
        'data/kansai_spots/hotels_midrange_budget_candidates.csv',
        'data/kansai_spots/hotels_onsen_area_candidates.csv',
    ]

    hotel_seen = {}
    hotel_sources = defaultdict(list)
    hotel_stats = defaultdict(int)

    print("\n\n[HOTELS]")
    for filepath in hotel_files:
        path = Path(filepath)
        if not path.exists():
            print(f"  [pending] {path.name}")
            continue

        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if not row.get('name_ja') or row['name_ja'].startswith('#'):
                    continue

                key = (row['name_ja'], row['city_code'])
                if key not in hotel_seen:
                    hotel_seen[key] = {
                        'name_ja': row['name_ja'],
                        'city_code': row['city_code'],
                        'area': row.get('area', ''),
                        'hotel_type': row.get('hotel_type', ''),
                        'price_level': row.get('price_level', 'moderate'),
                        'key_features': row.get('key_features', ''),
                        'source': row.get('source_url', row.get('source', '')),
                    }
                    hotel_sources[key].append(path.name)
                    count += 1
                else:
                    hotel_sources[key].append(path.name)

            hotel_stats[path.name] = count
            print(f"  [ok] {path.name:45} (+{count:3})")

    print(f"\n  TOTAL: {len(hotel_seen)} unique hotels")

    # Price distribution
    prices = defaultdict(int)
    h_cities = defaultdict(int)
    for (name, city), row in hotel_seen.items():
        prices[row['price_level']] += 1
        h_cities[city] += 1

    print("\n  [Price distribution]")
    for level in ['luxury', 'expensive', 'moderate', 'budget', 'backpacker']:
        count = prices[level]
        if count > 0:
            pct = count / len(hotel_seen) * 100
            print(f"    {level:10} {count:3} ({pct:5.1f}%)")

    # Multi-source
    h_multi_src = sum(1 for sources in hotel_sources.values() if len(sources) > 1)
    print(f"\n  [Confidence] {h_multi_src} hotels from 2+ sources ({h_multi_src/len(hotel_seen)*100:.1f}%)")

    # Write merged files
    print("\n\n[WRITING OUTPUTS]")

    with open('data/kansai_spots/restaurants_merged_final.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['name_ja', 'city_code', 'area', 'cuisine_type', 'budget_tier',
                     'tabelog_score', 'michelin', 'mention_count', 'source']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (name, city), row in sorted(rest_seen.items()):
            writer.writerow(row)
    print("  [ok] restaurants_merged_final.csv")

    with open('data/kansai_spots/hotels_merged_final.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['name_ja', 'city_code', 'area', 'hotel_type', 'price_level',
                     'key_features', 'source']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (name, city), row in sorted(hotel_seen.items()):
            writer.writerow(row)
    print("  [ok] hotels_merged_final.csv")

    # Final assessment
    print("\n\n" + "=" * 80)
    print("PHASE 1.5 FINAL ASSESSMENT")
    print("=" * 80)

    rest_pct = len(rest_seen) / 750 * 100
    hotel_pct = len(hotel_seen) / 550 * 100

    print(f"\nRestaurants: {len(rest_seen):3} / 700-800 target ({rest_pct:5.1f}%)")
    print(f"Hotels:      {len(hotel_seen):3} / 500-600 target ({hotel_pct:5.1f}%)")

    print("\n[GO/NO-GO DECISION]")

    checks = {
        "Restaurants >= 500": len(rest_seen) >= 500,
        "Hotels >= 350": len(hotel_seen) >= 350,
        "Budget balanced (±5%)": abs(budgets['luxury']/len(rest_seen)*100 - 22.5) < 5,
        "Multi-source >= 40%": multi_src / len(rest_seen) >= 0.4,
    }

    all_pass = True
    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        symbol = "[OK]" if result else "[NO]"
        print(f"  {symbol} {check}: {status}")
        if not result:
            all_pass = False

    print("\n[RECOMMENDATION]")
    if all_pass:
        print("  -> PROCEED TO PHASE 2")
        print("  Discovery pool is adequate and well-balanced.")
    else:
        print("  -> CONSIDER Phase 1.5.5 (Retty/GURUNAVI/Booking)")
        print("  Some metrics below target. Additional sources recommended.")


if __name__ == '__main__':
    merge_all()
