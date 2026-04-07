import json
import sys

# 四个文件
files = [
    "data/kansai_spots/kyoto_city.json",
    "data/kansai_spots/osaka_city.json",
    "data/kansai_spots/nara.json",
    "data/kansai_spots/hyogo.json"
]

all_spots = []

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'spots' in data:
                all_spots.extend(data['spots'])
                print(f"✓ {file_path.split('/')[-1]}: {len(data['spots'])} spots", file=sys.stderr)
    except Exception as e:
        print(f"✗ Error reading {file_path}: {e}", file=sys.stderr)

# Print header
print("="*180)
print("景点数据汇总表")
print("="*180)
print(f"{'ID':<30} | {'中文名':<20} | {'等级':<3} | {'城市':<10} | {'最佳季节':<8} | {'门票(JPY)':<10} | {'标签':<40} | {'Profile Boosts':<30}")
print("-"*180)

# Print each spot
for spot in all_spots:
    spot_id = spot.get('id', 'N/A')
    name_zh = spot.get('name_zh', 'N/A')
    grade = spot.get('grade', 'N/A')
    city_code = spot.get('city_code', 'N/A')
    best_season = spot.get('best_season', 'N/A')
    admission_jpy = str(spot.get('cost', {}).get('admission_jpy', 'N/A'))
    
    tags = spot.get('tags', [])
    tags_str = ', '.join(tags[:2]) if len(tags) > 2 else ', '.join(tags)
    
    profile_boosts = spot.get('profile_boosts', {})
    profile_keys = ', '.join(sorted(profile_boosts.keys()))
    
    print(f"{spot_id:<30} | {name_zh:<20} | {grade:<3} | {city_code:<10} | {best_season:<8} | {admission_jpy:<10} | {tags_str:<40} | {profile_keys:<30}")

print("-"*180)
print(f"总计: {len(all_spots)} 个景点")

