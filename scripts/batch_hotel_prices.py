"""
批量搜索酒店价格脚本
用 OpenCLI google search 搜索每家酒店的价格
搜索策略: 酒店名 + "料金" -> 从 Google 摘要提取价格

用法:
  .venv/Scripts/python.exe scripts/batch_hotel_prices.py
  .venv/Scripts/python.exe scripts/batch_hotel_prices.py --dry-run
  .venv/Scripts/python.exe scripts/batch_hotel_prices.py --limit 10
  .venv/Scripts/python.exe scripts/batch_hotel_prices.py --resume

输出: data/kansai_spots/hotels/prices_result.json
"""
import json
import subprocess
import re
import sys
import os
import time
import argparse

sys.stdout.reconfigure(encoding='utf-8')

OPENCLI = "node opencli-main/dist/main.js"
DATA_DIR = "data/kansai_spots/hotels"
OUTPUT = f"{DATA_DIR}/prices_result.json"
SKIP_FILES = ["osaka.json", "prices_result.json", "price_guide.json"]


def load_hotels():
    hotels = []
    for root, dirs, files in os.walk(DATA_DIR):
        for fname in files:
            if not fname.endswith('.json') or fname in SKIP_FILES:
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, encoding='utf-8') as f:
                data = json.load(f)
            for h in data.get('hotels', []):
                name = h.get('name_ja', '')
                if name:
                    hotels.append({
                        'name_ja': name,
                        'city_code': h.get('city_code', ''),
                        'hotel_type': h.get('hotel_type', ''),
                        'file': fpath,
                    })
    return hotels


def extract_prices(text):
    values = []
    for m in re.findall(r'[¥￥]([\d,]+)', text):
        val = int(m.replace(',', ''))
        if 1000 <= val <= 2000000:
            values.append(val)
    for m in re.findall(r'([\d,]+)円', text):
        val = int(m.replace(',', ''))
        if 1000 <= val <= 2000000:
            values.append(val)
    return sorted(set(values))


def search_google(query):
    try:
        r = subprocess.run(
            f'{OPENCLI} google search "{query}" --limit 5 --format json',
            shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8'
        )
        return r.stdout
    except:
        return ''


def search_hotel_price(name):
    # 策略1: 酒店名 + 料金
    output = search_google(f'{name} 料金 1泊')
    prices = extract_prices(output)

    # 策略2: 楽天トラベル
    if not prices:
        output2 = search_google(f'{name} 楽天トラベル 料金')
        prices = extract_prices(output2)

    # 策略3: 携程
    if not prices:
        output3 = search_google(f'{name} 携程 价格')
        prices = extract_prices(output3)

    if prices:
        return {
            'prices': prices,
            'min': prices[0],
            'max': prices[-1],
            'price_range': f'¥{prices[0]:,}-¥{prices[-1]:,}',
        }
    return {'prices': [], 'min': None, 'max': None, 'price_range': None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()

    hotels = load_hotels()
    print(f'Total: {len(hotels)} hotels (excluding osaka)')

    if args.dry_run:
        for h in hotels:
            print(f"  {h['name_ja']} | {h['city_code']} | {h['hotel_type']}")
        return

    # Resume: load existing results
    existing = {}
    if args.resume and os.path.exists(OUTPUT):
        with open(OUTPUT, encoding='utf-8') as f:
            for r in json.load(f):
                if r.get('price_range'):
                    existing[r['name_ja']] = r

    if args.limit:
        hotels = hotels[:args.limit]

    results = list(existing.values())
    search_count = 0

    for i, h in enumerate(hotels):
        name = h['name_ja']
        if name in existing:
            print(f'[{i+1}/{len(hotels)}] {name} ... skip (cached)')
            continue

        print(f'[{i+1}/{len(hotels)}] {name} ... ', end='', flush=True)
        price = search_hotel_price(name)

        if price['min']:
            print(price['price_range'])
        else:
            print('not found')

        results.append({
            'name_ja': name,
            'city_code': h['city_code'],
            'hotel_type': h['hotel_type'],
            'price_min': price['min'],
            'price_max': price['max'],
            'price_range': price['price_range'],
            'all_prices': price['prices'],
        })

        search_count += 1
        if search_count % 5 == 0:
            with open(OUTPUT, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        time.sleep(1.5)

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    found = sum(1 for r in results if r.get('price_min'))
    print(f'\nDone: {found}/{len(results)} with prices')
    print(f'Output: {OUTPUT}')


if __name__ == '__main__':
    main()
