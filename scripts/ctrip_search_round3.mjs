#!/usr/bin/env node
/**
 * Round 3: 对仍 unverified 的 134 家用"日文原文 + 英文名"做精准查询。
 *
 * 关键洞察：携程搜索中文"凯悦摄政京都"被错推上海，但日文"ハイアットリージェンシー京都"能精确命中。
 *
 * 策略：
 *   1. 日文原名去括号
 *   2. 括号内英文名（如 Hotel Granvia Kyoto）
 *   3. 强力 city 过滤：country!=日本 淘汰
 */
import fs from 'node:fs';
import path from 'node:path';

const [hotelsPath, finalMatchPath, outPath] = process.argv.slice(2);
const hotels = JSON.parse(fs.readFileSync(hotelsPath, 'utf-8'));
const bests = JSON.parse(fs.readFileSync(finalMatchPath, 'utf-8'));
const bestById = Object.fromEntries(bests.map(b => [b.our_id, b]));

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

function genQueries(hotel) {
  const qs = new Set();
  const ja = hotel.name_ja || '';
  const zh = hotel.name_zh || '';

  // 1. 日文全名（去括号）
  const jaNoParen = ja.replace(/\(.*?\)/g, '').replace(/（.*?）/g, '').trim();
  if (jaNoParen) qs.add(jaNoParen);

  // 2. 括号内英文名
  const enMatch = ja.match(/\(([A-Za-z][^)]+)\)/) || zh.match(/\(([A-Za-z][^)]+)\)/);
  if (enMatch) qs.add(enMatch[1].trim());

  // 3. 日文假名核心词（去掉「ホテル」「京都」等）
  if (jaNoParen) {
    const core = jaNoParen
      .replace(/ホテル|ホステル|アパート|旅館/g, '')
      .replace(/京都|大阪|神戸|奈良|有馬|高野山|城崎|白浜/g, '')
      .trim();
    if (core && core.length >= 2 && core !== jaNoParen) qs.add(core);
  }

  return [...qs].slice(0, 3);
}

(async () => {
  const unv = hotels.filter(h => bestById[h.id]?.unverified);
  console.log(`Round 3 retrying ${unv.length} still-unverified hotels (using Japanese + English names)`);

  const results = [];
  const start = Date.now();
  for (let i = 0; i < unv.length; i++) {
    const h = unv[i];
    const queries = genQueries(h);
    const allMatches = [];
    for (const q of queries) {
      if (!q) continue;
      try {
        const r = await searchOne(q);
        const hotels = r
          .filter(m => (m.type === 'Hotel' || m.displayType === '酒店'))
          .filter(m => {
            // 硬过滤：必须日本
            const c = (m.countryName || '').toLowerCase();
            if (c && c !== '日本' && !c.includes('japan')) return false;
            return true;
          });
        for (const x of hotels.slice(0, 3)) {
          allMatches.push({ ...x, __query: q });
        }
      } catch (e) {
        process.stderr.write(`  err "${q}": ${e.message}\n`);
      }
      await new Promise(r => setTimeout(r, 250));
    }
    results.push({
      our_id: h.id,
      our_name_zh: h.name_zh,
      our_name_ja: h.name_ja,
      our_city: h.city,
      queries,
      match_count: allMatches.length,
      matches: allMatches.slice(0, 6).map(m => ({
        id: m.id, word: m.word, eName: m.eName,
        displayName: m.displayName, displayType: m.displayType,
        cityId: m.cityId, cityName: m.cityName,
        countryName: m.countryName, gLat: m.gLat, gLon: m.gLon,
        __query: m.__query
      }))
    });
    if (i % 10 === 0) {
      const elapsed = (Date.now() - start) / 1000;
      const rate = (i + 1) / elapsed;
      process.stderr.write(`[${i + 1}/${unv.length}] ${h.name_zh.slice(0,20)} → ${allMatches.length} hits | ${rate.toFixed(1)}/s\n`);
    }
  }

  fs.writeFileSync(outPath, JSON.stringify(results, null, 2), 'utf-8');
  const withHits = results.filter(r => r.match_count > 0).length;
  console.log(`Done. ${withHits}/${results.length} records now have Japan-filtered matches`);
})();
