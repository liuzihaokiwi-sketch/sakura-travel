/**
 * Xiaohongshu dump-state — dev utility to dump page state for a note.
 *
 * Writes __INITIAL_STATE__ (if present) plus HTML/inline-script snapshots to
 * an output directory so we can reverse-engineer the current data shape when
 * the DOM adapters go stale.
 *
 * Usage:
 *   opencli xiaohongshu dump-state <note-id-or-url> --output ./dump
 */

import * as fs from 'fs';
import * as path from 'path';

import { cli, Strategy } from '../../registry.js';
import { buildNoteUrl, parseNoteId } from './note-helpers.js';

cli({
  site: 'xiaohongshu',
  name: 'dump-state',
  description: '开发用:导出笔记页面的 __INITIAL_STATE__ 和 HTML 快照',
  domain: 'www.xiaohongshu.com',
  strategy: Strategy.COOKIE,
  args: [
    { name: 'note-id', positional: true, required: true, help: 'Note ID, full URL, or short link' },
    { name: 'output', default: './xhs-dump', help: 'Output directory' },
  ],
  columns: ['file', 'bytes'],
  func: async (page, kwargs) => {
    const raw = String(kwargs['note-id']);
    const noteId = parseNoteId(raw);
    const output = String(kwargs.output);

    await page.goto(buildNoteUrl(raw));
    await page.wait(3);

    const snapshot = await page.evaluate(`
      (() => {
        const out = { noteId: '${noteId}', url: location.href };

        // __INITIAL_STATE__ (main hydration source)
        try {
          out.initialState = window.__INITIAL_STATE__ ? JSON.parse(JSON.stringify(window.__INITIAL_STATE__)) : null;
        } catch (e) { out.initialStateError = String(e); }

        // All inline scripts that look relevant (keep first 50KB each to avoid bloat)
        const scripts = [];
        document.querySelectorAll('script').forEach((s, i) => {
          const txt = s.textContent || '';
          if (!txt) return;
          if (/__INITIAL_STATE__|noteDetailMap|imageList|videoInfoV2|xhscdn|sns-video/.test(txt)) {
            scripts.push({ idx: i, length: txt.length, head: txt.slice(0, 50000) });
          }
        });
        out.scripts = scripts;

        // Image elements currently in DOM
        out.imgElements = Array.from(document.querySelectorAll('img')).slice(0, 50).map(img => ({
          src: img.src || '',
          dataSrc: img.getAttribute('data-src') || '',
          className: img.className || '',
        }));

        // Background-image URLs on likely carriers
        const bgHosts = [];
        document.querySelectorAll('[style*="background-image"]').forEach((el, i) => {
          if (i > 40) return;
          const bg = el.style?.backgroundImage || '';
          if (bg) bgHosts.push({ cls: el.className || '', bg });
        });
        out.backgroundImages = bgHosts;

        // Raw HTML head portion so we can see meta-og image etc.
        out.headHtml = document.head.outerHTML.slice(0, 30000);

        return out;
      })()
    `);

    fs.mkdirSync(output, { recursive: true });
    const resolved = (snapshot as any)?.noteId || noteId;
    const outPath = path.join(output, `${resolved}.json`);
    const json = JSON.stringify(snapshot, null, 2);
    fs.writeFileSync(outPath, json, 'utf8');

    return [{ file: outPath, bytes: json.length }];
  },
});
