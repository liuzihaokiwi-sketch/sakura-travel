#!/usr/bin/env node
/**
 * 批量调携程 gaHotelSearchEngine API
 * 用法：node ctrip_search_batch.mjs <hotels_json> <out_json>
 *
 * 输入：hotels__kansai.json
 * 输出：每家酒店 { our_id, query, matched: [{id, word, eName, gLat, gLon, cityName, type}] }
 */
import fs from 'node:fs';
import path from 'node:path';

const [hotelsPath, outPath] = process.argv.slice(2);
if (!hotelsPath || !outPath) {
  console.error('Usage: node ctrip_search_batch.mjs <hotels_json> <out_json>');
  process.exit(1);
}

const hotels = JSON.parse(fs.readFileSync(hotelsPath, 'utf-8'));
console.log(`Loaded ${hotels.length} hotels`);

async function searchOne(keyword) {
  const body = {
    keyword,
    searchType: 'D',
    platform: 'online',
    pageID: '102001',
    head: {
      Locale: 'zh-CN',
      LocaleController: 'zh_cn',
      Currency: 'CNY',
      PageId: '102001',
      clientID: 'opencli-ctrip-search',
      group: 'ctrip',
      Frontend: { sessionID: 1, pvid: 1 },
      HotelExtension: { group: 'CTRIP', WebpSupport: false }
    }
  };
  const r = await fetch('https://m.ctrip.com/restapi/soa2/21881/json/gaHotelSearchEngine', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const j = await r.json();
  if (j.ResponseStatus?.Ack !== 'Success') throw new Error(`API: ${JSON.stringify(j.ResponseStatus?.Errors)}`);
  return j.Response?.searchResults || [];
}

function pickQuery(hotel) {
  // 优先用 name_zh；若含括号/长英文名则取括号前
  let q = hotel.name_zh || hotel.name_ja || hotel.name || '';
  q = q.split('(')[0].split('（')[0].trim();
  return q;
}

const results = [];
const startTime = Date.now();
for (let i = 0; i < hotels.length; i++) {
  const h = hotels[i];
  const q = pickQuery(h);
  try {
    const matches = await searchOne(q);
    const onlyHotels = matches.filter(m => m.type === 'Hotel' || m.displayType === '酒店');
    results.push({
      our_id: h.id,
      our_name_zh: h.name_zh,
      our_name_ja: h.name_ja,
      our_city: h.city,
      our_area: h.area,
      our_budget_tier: h.budget_tier,
      query: q,
      match_count: matches.length,
      hotel_match_count: onlyHotels.length,
      matches: onlyHotels.slice(0, 5).map(m => ({
        id: m.id,
        word: m.word,
        eName: m.eName,
        displayName: m.displayName,
        displayType: m.displayType,
        cityId: m.cityId,
        cityName: m.cityName,
        countryName: m.countryName,
        gLat: m.gLat,
        gLon: m.gLon,
        cStar: m.cStar,
        commentScore: m.commentScore
      }))
    });
    if (i % 20 === 0) {
      const elapsed = (Date.now() - startTime) / 1000;
      const rate = (i + 1) / elapsed;
      const eta = ((hotels.length - i - 1) / rate).toFixed(0);
      process.stderr.write(`[${i + 1}/${hotels.length}] q="${q}" → ${onlyHotels.length} hotels | rate=${rate.toFixed(1)}/s eta=${eta}s\n`);
    }
  } catch (e) {
    results.push({
      our_id: h.id,
      our_name_zh: h.name_zh,
      query: q,
      error: String(e.message || e)
    });
    process.stderr.write(`[${i + 1}/${hotels.length}] ERROR q="${q}": ${e.message}\n`);
  }
  // 限速：200ms 间隔，避免风控
  await new Promise(r => setTimeout(r, 200));
}

fs.writeFileSync(outPath, JSON.stringify(results, null, 2), 'utf-8');
console.log(`Done. ${results.length} records → ${outPath}`);
console.log(`Elapsed: ${((Date.now() - startTime) / 1000).toFixed(1)}s`);

// 统计
const withMatch = results.filter(r => r.hotel_match_count > 0).length;
const noMatch = results.filter(r => !r.error && r.hotel_match_count === 0).length;
const errors = results.filter(r => r.error).length;
console.log(`Summary: matched=${withMatch} no_match=${noMatch} errors=${errors}`);
