#!/usr/bin/env python
"""
Detailed balance analysis for Phase 1.5 discovery pool.
Identifies gaps in city×cuisine×budget combinations.
"""
import csv
from collections import defaultdict

def analyze_restaurants():
    """Analyze restaurant pool balance by decision unit."""

    print("=" * 80)
    print("RESTAURANT POOL BALANCE ANALYSIS")
    print("=" * 80)

    # Try final merged file first, fall back to temp version
    try:
        filepath = 'data/kansai_spots/restaurants_merged_final.csv'
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"\n[input] {filepath} ({len(rows)} entries)")
    except FileNotFoundError:
        filepath = 'data/kansai_spots/restaurants_merged.csv'
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"\n[input] {filepath} ({len(rows)} entries)")

    # Organize by decision unit: city × cuisine × budget_tier
    units = defaultdict(list)
    for row in rows:
        city = row['city_code']
        cuisine = row.get('cuisine_type', 'unknown')
        budget = row.get('budget_tier', 'unknown')
        key = (city, cuisine, budget)
        units[key].append(row)

    # Analysis
    print(f"\n[coverage] Total decision units: {len(units)}")

    # Find under-served units (<3 entries)
    underserved = {k: v for k, v in units.items() if len(v) < 3}
    overserved = {k: v for k, v in units.items() if len(v) > 5}

    print(f"  - Well-served (3-5): {len([u for u in units.values() if 3 <= len(u) <= 5])}")
    print(f"  - Under-served (<3): {len(underserved)} units")
    print(f"  - Over-served (>5): {len(overserved)} units")

    if underserved:
        print(f"\n[gap-analysis] Under-served combinations (need more options):")
        # Group by city
        by_city = defaultdict(list)
        for (city, cuisine, budget), entries in sorted(underserved.items()):
            by_city[city].append((cuisine, budget, len(entries)))

        for city in sorted(by_city.keys()):
            print(f"\n  {city}:")
            for cuisine, budget, count in sorted(by_city[city]):
                indicator = "!" if count == 1 else "~"
                print(f"    {indicator} {cuisine:20} | {budget:8} | {count} option")

    # City-level analysis
    print(f"\n[city-balance]")
    city_counts = defaultdict(int)
    city_budgets = defaultdict(lambda: defaultdict(int))
    for row in rows:
        city = row['city_code']
        budget = row.get('budget_tier', 'unknown')
        city_counts[city] += 1
        city_budgets[city][budget] += 1

    print("\nCity         | Total | Luxury | Mid | Budget | Street | %Luxury")
    print("-" * 65)
    for city in sorted(city_counts.keys()):
        total = city_counts[city]
        lux = city_budgets[city].get('luxury', 0)
        mid = city_budgets[city].get('mid', 0)
        bud = city_budgets[city].get('budget', 0)
        st = city_budgets[city].get('street', 0)
        lux_pct = lux / total * 100 if total > 0 else 0

        threshold = "OK" if 20 <= lux_pct <= 35 else "IMBALANCED"
        print(f"{city:12} | {total:5} | {lux:6} | {mid:3} | {bud:6} | {st:6} | {lux_pct:5.1f}% [{threshold}]")

    # Global distribution
    print(f"\n[global-distribution]")
    global_budgets = defaultdict(int)
    for row in rows:
        budget = row.get('budget_tier', 'unknown')
        global_budgets[budget] += 1

    total = len(rows)
    for budget in ['luxury', 'expensive', 'mid', 'budget', 'street', 'unknown']:
        count = global_budgets[budget]
        if count > 0:
            pct = count / total * 100
            target = {
                'luxury': '20-25%',
                'expensive': '5-10%',
                'mid': '30-35%',
                'budget': '20-25%',
                'street': '15-20%'
            }.get(budget, 'varies')
            print(f"  {budget:10} {count:3} ({pct:5.1f}%) target: {target}")

    # Cuisine diversity by city
    print(f"\n[cuisine-diversity]")
    cuisines_per_city = defaultdict(set)
    for row in rows:
        city = row['city_code']
        cuisine = row.get('cuisine_type', 'unknown')
        if cuisine:
            cuisines_per_city[city].add(cuisine)

    for city in sorted(cuisines_per_city.keys()):
        count = len(cuisines_per_city[city])
        cuisines = ', '.join(sorted(cuisines_per_city[city])[:5]) + ('...' if count > 5 else '')
        print(f"  {city:15} {count:2} cuisines: {cuisines}")

    print(f"\n[recommendation]")
    if len(underserved) > 20:
        print("  WARNING: Too many under-served units. May need another round.")
    elif len(underserved) > 10:
        print("  CAUTION: Some gaps exist. Manageable with editorial choice.")
    else:
        print("  GOOD: Most units have 3+ options for editorial selection.")


if __name__ == '__main__':
    analyze_restaurants()
    print("\n[done]")
