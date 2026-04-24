/**
 * Xiaohongshu download — download images and videos from a note.
 *
 * Usage:
 *   opencli xiaohongshu download <note-id-or-url> --output ./xhs
 *
 * Accepts a bare note ID, a full xiaohongshu.com URL (with xsec_token),
 * or a short link (http://xhslink.com/...).
 */

import { cli, Strategy } from '../../registry.js';
import { formatCookieHeader } from '../../download/index.js';
import { downloadMedia } from '../../download/media-download.js';
import { buildNoteUrl, parseNoteId } from './note-helpers.js';

cli({
  site: 'xiaohongshu',
  name: 'download',
  description: '下载小红书笔记中的图片和视频',
  domain: 'www.xiaohongshu.com',
  strategy: Strategy.COOKIE,
  args: [
    { name: 'note-id', positional: true, required: true, help: 'Note ID, full URL, or short link' },
    { name: 'output', default: './xiaohongshu-downloads', help: 'Output directory' },
  ],
  columns: ['index', 'type', 'status', 'size'],
  func: async (page, kwargs) => {
    const rawInput = String(kwargs['note-id']);
    const output = kwargs.output;
    const noteId = parseNoteId(rawInput);

    await page.goto(buildNoteUrl(rawInput));

    // Extract note info and media URLs
    //
    // Strategy (2026-04): XHS note pages hydrate their Vue app from an inline
    // `window.__INITIAL_STATE__ = {...}` assignment inside a <script>. The
    // live window object is a reactive proxy with circular refs (JSON.stringify
    // fails), so we parse the raw script text instead and pull image/video URLs
    // by regex. Falls back to DOM scraping if the inline state is missing.
    const data = await page.evaluate(`
      (() => {
        const result = {
          noteId: '${noteId}',
          title: '',
          author: '',
          media: []
        };
        const seenMedia = new Set();
        const pushMedia = (type, url) => {
          if (!url) return;
          const key = type + ':' + url;
          if (seenMedia.has(key)) return;
          seenMedia.add(key);
          result.media.push({ type, url });
        };

        const locationMatch = (location.pathname || '').match(/\\/(?:explore|note|search_result|discovery\\/item)\\/([a-f0-9]+)/i);
        if (locationMatch) {
          result.noteId = locationMatch[1];
        }

        // Title / author via meta or DOM fallback
        const titleEl = document.querySelector('#detail-title, .title, meta[property="og:title"]');
        result.title = (titleEl?.getAttribute?.('content') || titleEl?.textContent || '').trim() || 'untitled';
        const authorEl = document.querySelector('.username, .author-wrapper .name, .author-name');
        result.author = authorEl?.textContent?.trim() || 'unknown';

        // Find the inline script that declares __INITIAL_STATE__
        let stateScript = '';
        document.querySelectorAll('script').forEach(s => {
          const t = s.textContent || '';
          if (t.includes('__INITIAL_STATE__') && t.length > stateScript.length) {
            stateScript = t;
          }
        });

        const decode = (u) => String(u || '').replace(/\\\\u002F/g, '/').replace(/\\\\\\//g, '/');
        const normalizeImage = (u) => {
          let out = decode(u);
          if (!out) return '';
          // Strip query strings that cap size/quality; keep the raw path
          out = out.split('?')[0];
          return out;
        };

        if (stateScript) {
          // --- Images ---
          // Each note image appears as an entry in an "imageList" array, with
          // concrete CDN URLs in "infoList":[{"imageScene":"WB_DFT"|"WB_PRV","url":"..."}].
          // We can't reliably bound the outer imageList array with a regex
          // (infoList has its own brackets), so instead we walk all scene/url
          // pairs in the script, but only keep ones that sit between the first
          // "imageList" and the next "videoInfoV2"/"interactInfo" marker —
          // enough to avoid false positives from other arrays.
          const imgStart = stateScript.indexOf('"imageList":');
          let imgEnd = stateScript.length;
          for (const marker of ['"videoInfoV2"', '"video":{', '"interactInfo"']) {
            const p = stateScript.indexOf(marker, imgStart + 1);
            if (p > imgStart && p < imgEnd) imgEnd = p;
          }
          if (imgStart >= 0) {
            const slice = stateScript.slice(imgStart, imgEnd);
            const infoRe = /\\{"imageScene":"([^"\\\\]+)","url":"([^"]+)"\\}/g;
            // Group URLs by position so preview/default stay paired per image.
            // We pick one URL per imageList entry: prefer WB_DFT, else WB_PRV.
            const groups = []; // [{WB_DFT, WB_PRV, OTHER}]
            let current = null;
            let lastIndex = -1;
            let m;
            while ((m = infoRe.exec(slice)) !== null) {
              const scene = m[1];
              const url = normalizeImage(m[2]);
              if (!url) continue;
              // Heuristic: if more than ~400 chars since last match, start a new image group.
              if (!current || m.index - lastIndex > 800) {
                current = {};
                groups.push(current);
              }
              if (!current[scene]) current[scene] = url;
              lastIndex = m.index;
            }
            for (const g of groups) {
              const pick = g.WB_DFT || g.WB_PRV || Object.values(g)[0];
              if (pick) pushMedia('image', pick);
            }
          }

          // --- Video ---
          // h264 stream entries expose masterUrl + backupUrls arrays. Grab the
          // first masterUrl per stream (top quality), fall back to first backup.
          const streamRe = /"masterUrl":"([^"]+)"/g;
          let vm;
          while ((vm = streamRe.exec(stateScript)) !== null) {
            pushMedia('video', decode(vm[1]));
          }
          if (result.media.filter(x => x.type === 'video').length === 0) {
            const backupRe = /"backupUrls":\\[\\s*"([^"]+)"/g;
            let bm;
            while ((bm = backupRe.exec(stateScript)) !== null) {
              pushMedia('video', decode(bm[1]));
            }
          }
        }

        // Fallback: DOM <img> scrape for non-video notes if state-based extraction yielded nothing
        if (result.media.length === 0) {
          const imgSet = new Set();
          document.querySelectorAll('img').forEach(img => {
            const src = img.src || img.getAttribute('data-src') || '';
            if (src && /xhscdn|xiaohongshu/.test(src) && !/avatar|emoji|header-logo|qrcode/i.test(img.className || '')) {
              imgSet.add(normalizeImage(src));
            }
          });
          imgSet.forEach(u => pushMedia('image', u));

          document.querySelectorAll('video source, video[src]').forEach(v => {
            const src = v.src || v.getAttribute('src') || '';
            if (src && !src.startsWith('blob:')) pushMedia('video', src);
          });
        }

        return result;
      })()
    `);

    if (!data || !data.media || data.media.length === 0) {
      return [{ index: 0, type: '-', status: 'failed', size: 'No media found' }];
    }

    // Extract cookies for authenticated downloads
    const cookies = formatCookieHeader(await page.getCookies({ domain: 'xiaohongshu.com' }));
    const resolvedNoteId = typeof data.noteId === 'string' && data.noteId.trim()
      ? data.noteId.trim()
      : noteId;

    return downloadMedia(data.media, {
      output,
      subdir: resolvedNoteId,
      cookies,
      filenamePrefix: resolvedNoteId,
      timeout: 60000,
    });
  },
});
