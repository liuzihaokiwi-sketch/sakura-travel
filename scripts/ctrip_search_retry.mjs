#!/usr/bin/env node
/**
 * Phase A2: 对 unverified 酒店做多查询策略补救。
 * 输入：hotels__kansai.json + ctrip_best_match.json
 * 输出：ctrip_matched_retry.json (扩展 matches 数组)
 */
import fs from 'node:fs';

const [hotelsPath, bestMatchPath, outPath] = process.argv.slice(2);
const hotels = JSON.parse(fs.readFileSync(hotelsPath, 'utf-8'));
const bests = JSON.parse(fs.readFileSync(bestMatchPath, 'utf-8'));
const bestById = Object.fromEntries(bests.map(b => [b.our_id, b]));

const CITY_HINT = {
  kyoto: '京都', osaka: '大阪', kobe: '神户',
  nara: '奈良', arima: '有马', kinosaki: '城崎',
  koyasan: '高野山', shirahama: '白浜'
};

async function searchOne(keyword) {
  const body = {
    keyword, searchType: 'D', platform: 'online', pageID: '102001',
    head: {
      Locale: 'zh-CN', LocaleController: 'zh_cn', Currency: 'CNY', PageId: '102001',
      clientID: 'opencli-ctrip-search', group: 'ctrip',
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
  return j.Response?.searchResults || [];
}

function genFallbackQueries(hotel) {
  const name_zh = hotel.name_zh || '';
  const name_ja = hotel.name_ja || '';
  const city_cn = CITY_HINT[hotel.city] || '';
  const queries = new Set();

  // 策略 1：日文名（全）
  if (name_ja && name_ja !== name_zh) {
    const jaCore = name_ja.split('(')[0].split('（')[0].trim();
    if (jaCore) queries.add(jaCore);
  }

  // 策略 2：核心品牌词 + 城市
  const name = name_zh || name_ja;
  if (name) {
    // 去除括号内容
    let core = name.replace(/\(.*?\)/g, '').replace(/（.*?）/g, '').trim();
    // 中文名常见模式"<品牌>酒店<区域>"
    // 取前 4 个中文字符或前 2 个英文词
    let shortCore;
    const isAscii = /^[a-zA-Z0-9\s]+/.test(core);
    if (isAscii) {
      shortCore = core.split(/\s+/).slice(0, 2).join(' ');
    } else {
      // 找中文品牌词：常见前缀去掉城市/描述词
      shortCore = core
        .replace(/京都|大阪|神户|奈良|有马|高野山|城崎|白浜|白滨/g, '')
        .replace(/酒店|饭店|旅馆|宾馆|度假村|公寓|民宿|hotel|Hotel/gi, '')
        .trim();
      // 前 4 字
      shortCore = shortCore.slice(0, 4);
    }
    if (shortCore && shortCore.length >= 2) {
      queries.add(`${shortCore} ${city_cn}`.trim());
      queries.add(shortCore);
    }
  }

  // 策略 3：英文名核心
  const enMatch = name_ja.match(/\(([A-Za-z][^)]+)\)/);
  if (enMatch) {
    const enCore = enMatch[1].trim().split(/\s+/).slice(0, 2).join(' ');
    queries.add(enCore);
    queries.add(`${enCore} ${city_cn}`.trim());
  }

  return [...queries].slice(0, 4);
}

async function retry(hotel, best) {
  const queries = genFallbackQueries(hotel);
  const allMatches = [];
  for (const q of queries) {
    if (!q) continue;
    try {
      const results = await searchOne(q);
      const hotels = results.filter(m => m.type === 'Hotel' || m.displayType === '酒店');
      for (const h of hotels.slice(0, 3)) {
        allMatches.push({
          ...h,
          __query: q
        });
      }
    } catch (e) {
      process.stderr.write(`  retry error on "${q}": ${e.message}\n`);
    }
    await new Promise(r => setTimeout(r, 250));
  }
  return { tried_queries: queries, matches: allMatches };
}

(async () => {
  const unverified = hotels.filter(h => bestById[h.id]?.unverified);
  console.log(`Retrying ${unverified.length} unverified hotels`);

  const results = [];
  const start = Date.now();
  for (let i = 0; i < unverified.length; i++) {
    const h = unverified[i];
    const b = bestById[h.id];
    const { tried_queries, matches } = await retry(h, b);
    results.push({
      our_id: h.id,
      our_name_zh: h.name_zh,
      our_name_ja: h.name_ja,
      our_city: h.city,
      our_area: h.area,
      our_budget_tier: h.budget_tier,
      original_match_score: b.match_score,
      tried_queries,
      match_count: matches.length,
      matches: matches.slice(0, 8).map(m => ({
        id: m.id, word: m.word, eName: m.eName, displayName: m.displayName,
        displayType: m.displayType, cityId: m.cityId, cityName: m.cityName,
        countryName: m.countryName, gLat: m.gLat, gLon: m.gLon,
        cStar: m.cStar, commentScore: m.commentScore,
        __query: m.__query
      }))
    });
    if (i % 10 === 0) {
      const elapsed = (Date.now() - start) / 1000;
      const rate = (i + 1) / elapsed;
      process.stderr.write(`[${i + 1}/${unverified.length}] ${h.name_zh} → ${matches.length} hits | ${rate.toFixed(1)}/s\n`);
    }
  }

  fs.writeFileSync(outPath, JSON.stringify(results, null, 2), 'utf-8');
  const withHits = results.filter(r => r.match_count > 0).length;
  console.log(`Done. ${withHits}/${results.length} retried records now have matches`);
})();
