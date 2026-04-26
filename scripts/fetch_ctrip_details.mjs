#!/usr/bin/env node
/**
 * Phase C: 对命中的酒店批量抓详情页 HTML
 * 输入：ctrip_final_match.json
 * 输出：d:/tmp/ctrip_details/{hotel_id}.html
 */
import fs from 'node:fs';
import path from 'node:path';

const [matchPath, outDir] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });

const matches = JSON.parse(fs.readFileSync(matchPath, 'utf-8'));
// 只下载已命中的（unverified=false），unverified 不下载（按硬规不瞎猜）
const toFetch = matches.filter(m => !m.unverified && m.ctrip_id);
console.log(`Fetching details for ${toFetch.length} matched hotels`);

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36';

async function fetchOne(ctripId) {
  const url = `https://hotels.ctrip.com/hotels/detail/?hotelId=${ctripId}`;
  const r = await fetch(url, {
    headers: {
      'User-Agent': UA,
      'Accept': 'text/html,application/xhtml+xml',
      'Accept-Language': 'zh-CN,zh;q=0.9'
    }
  });
  return r.text();
}

let done = 0;
const start = Date.now();
for (const m of toFetch) {
  const fn = path.join(outDir, `${m.ctrip_id}.html`);
  if (fs.existsSync(fn)) {
    done++;
    continue;
  }
  try {
    const html = await fetchOne(m.ctrip_id);
    fs.writeFileSync(fn, html, 'utf-8');
    done++;
    if (done % 10 === 0) {
      const elapsed = (Date.now() - start) / 1000;
      const rate = done / elapsed;
      const eta = ((toFetch.length - done) / rate).toFixed(0);
      process.stderr.write(`[${done}/${toFetch.length}] ${m.our_id} (${m.ctrip_id}) rate=${rate.toFixed(1)}/s eta=${eta}s\n`);
    }
  } catch (e) {
    process.stderr.write(`ERROR ${m.our_id}/${m.ctrip_id}: ${e.message}\n`);
  }
  await new Promise(r => setTimeout(r, 400));  // 400ms 限速
}
console.log(`Done. ${done} files in ${outDir}`);
