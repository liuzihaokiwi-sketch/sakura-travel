#!/usr/bin/env python
"""
Merge restaurant candidates with schema normalization.
"""
import csv
from collections import defaultdict
from pathlib import Path

def merge_restaurants():
    """Merge all restaurant files with proper schema alignment."""

    # Load high-end candidates
    high_end_rows = []
    with open('data/kansai_spots/restaurants_candidate_pool.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['name_ja']:
                # Normalize schema
                normalized = {
                    'name_ja': row['name_ja'],
                    'city_code': row['city_code'],
                    'area': row['area'],
                    'cuisine_type': row.get('cuisine', ''),
                    'budget_tier': 'luxury',  # High-end are all luxury
                    'tabelog_score': row.get('tabelog_score', ''),
                    'michelin': row.get('michelin', ''),
                    'source': 'tabelog',
                    'notes': row.get('extra_info', '')
                }
                high_end_rows.append(normalized)

    # Load mid/budget candidates from both files
    mid_budget_rows = []
    for filepath in ['data/kansai_spots/restaurants_mid_budget_street.csv',
                     'data/kansai_spots/restaurants_mid_budget_candidates.csv']:
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('name_ja') and not row['name_ja'].startswith('#'):
                    normalized = {
                        'name_ja': row['name_ja'],
                        'city_code': row['city_code'],
                        'area': row['area'],
                        'cuisine_type': row.get('cuisine_type', ''),
                        'budget_tier': row.get('budget_tier', 'mid'),
                        'tabelog_score': row.get('tabelog_score', ''),
                        'michelin': '',
                        'source': row.get('source_url', row.get('source', '')),
                        'notes': row.get('brief_note', '')
                    }
                    mid_budget_rows.append(normalized)

    # Deduplicate
    seen = {}  # key: (name_ja, city_code)

    for row in high_end_rows + mid_budget_rows:
        key = (row['name_ja'], row['city_code'])
        if key not in seen:
            seen[key] = row

    # Analysis
    print("[MERGE] High-end: %d, Mid/Budget: %d, After dedup: %d unique" %
          (len(high_end_rows), len(mid_budget_rows), len(seen)))

    # Write merged file
    with open('data/kansai_spots/restaurants_merged.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['name_ja', 'city_code', 'area', 'cuisine_type', 'budget_tier',
                     'tabelog_score', 'michelin', 'source', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (name, city), row in sorted(seen.items()):
            writer.writerow(row)

    # Analysis by city and budget
    print("\n[BALANCE] Current state (before new agents):")
    balance = defaultdict(lambda: defaultdict(int))
    for row in seen.values():
        balance[row['city_code']][row['budget_tier']] += 1

    print("\nCity        | luxury | expensive | mid | budget | street | Total")
    print("-" * 65)
    for city in sorted(balance.keys()):
        l = balance[city].get('luxury', 0)
        e = balance[city].get('expensive', 0)
        m = balance[city].get('mid', 0)
        b = balance[city].get('budget', 0)
        s = balance[city].get('street', 0)
        total = l + e + m + b + s
        print("%-11s | %6d | %9d | %3d | %6d | %6d | %5d" % (city, l, e, m, b, s, total))

    # Distribution stats
    totals = {}
    for tier in ['luxury', 'expensive', 'mid', 'budget', 'street']:
        totals[tier] = sum(balance[c].get(tier, 0) for c in balance)

    grand_total = sum(totals.values())
    print("-" * 65)
    print("%-11s | %6d | %9d | %3d | %6d | %6d | %5d" %
          ('TOTAL', totals.get('luxury', 0), totals.get('expensive', 0),
           totals.get('mid', 0), totals.get('budget', 0), totals.get('street', 0),
           grand_total))

    print("\n[DISTRIBUTION]")
    for tier in ['luxury', 'expensive', 'mid', 'budget', 'street']:
        count = totals.get(tier, 0)
        pct = (count / grand_total * 100) if grand_total > 0 else 0
        print("  %10s: %3d entries (%5.1f%%)" % (tier, count, pct))

    print("\n[STATUS]")
    print("  Current: %d restaurants (target: 700-800)" % grand_total)
    if grand_total < 400:
        print("  -> Waiting for Tabelog (+150), Trip/XHS (+100) agents")
    elif grand_total < 600:
        print("  -> May need additional round after current agents complete")

if __name__ == '__main__':
    merge_restaurants()
