/**
 * Xiaohongshu note — read full note content from a public note page.
 *
 * Extracts title, author, description text, and engagement metrics
 * (likes, collects, comment count) via DOM extraction.
 */

import { cli, Strategy } from '../../registry.js';
import { AuthRequiredError, EmptyResultError } from '../../errors.js';
import { parseNoteId, buildNoteUrl } from './note-helpers.js';

cli({
  site: 'xiaohongshu',
  name: 'note',
  description: '获取小红书笔记正文和互动数据',
  domain: 'www.xiaohongshu.com',
  strategy: Strategy.COOKIE,
  args: [
    { name: 'note-id', required: true, positional: true, help: 'Note ID or full URL (preserves xsec_token for access)' },
  ],
  columns: ['field', 'value'],
  func: async (page, kwargs) => {
    const raw = String(kwargs['note-id']);
    const noteId = parseNoteId(raw);
    const url = buildNoteUrl(raw);

    await page.goto(url);
    await page.wait(3);

    const data = await page.evaluate(`
      (() => {
        const bodyText = document.body.innerText || '';
        const loginWall = /登录后查看|请登录/.test(bodyText);
        const notFound = /页面不见了|笔记不存在|无法浏览/.test(bodyText);

        const clean = (el) => (el?.textContent || '').replace(/\\s+/g, ' ').trim();

        // DOM-scraped values (may be empty on the current XHS build)
        let title = clean(document.querySelector('#detail-title, .title'));
        let desc = clean(document.querySelector('#detail-desc, .desc, .note-text'));
        let author = clean(document.querySelector('.username, .author-wrapper .name'));
        let likes = clean(document.querySelector('.like-wrapper .count'));
        let collects = clean(document.querySelector('.collect-wrapper .count'));
        let comments = clean(document.querySelector('.chat-wrapper .count'));

        // Fallback: parse the inline __INITIAL_STATE__ script text directly.
        // The reactive window.__INITIAL_STATE__ object has circular refs, but the
        // raw script body is plain JSON-ish text we can regex-match.
        let stateScript = '';
        document.querySelectorAll('script').forEach(s => {
          const t = s.textContent || '';
          if (t.includes('__INITIAL_STATE__') && t.length > stateScript.length) stateScript = t;
        });

        const pick = (re) => {
          const m = stateScript.match(re);
          return m ? m[1] : '';
        };
        // JSON in the script may contain \\uXXXX escapes; decode them for display.
        const jsonDecode = (s) => {
          if (!s) return '';
          try {
            return JSON.parse('"' + s.replace(/"/g, '\\\\"') + '"');
          } catch (e) { return s; }
        };

        if (stateScript) {
          if (!title) title = jsonDecode(pick(/"title":"([^"\\\\]*(?:\\\\.[^"\\\\]*)*)"/));
          if (!desc) desc = jsonDecode(pick(/"desc":"([^"\\\\]*(?:\\\\.[^"\\\\]*)*)"/));
          if (!author) author = jsonDecode(pick(/"nickname":"([^"\\\\]*(?:\\\\.[^"\\\\]*)*)"/)
            || pick(/"userInfo":\\{[^}]*?"nickname":"([^"\\\\]*)"/));
          if (!likes) likes = jsonDecode(pick(/"likedCount":"([^"]+)"/));
          if (!collects) collects = jsonDecode(pick(/"collectedCount":"([^"]+)"/));
          if (!comments) comments = jsonDecode(pick(/"commentCount":"([^"]+)"/));
        }

        // Tags
        const tags = [];
        document.querySelectorAll('#detail-desc a.tag, #detail-desc a[href*="search_result"]').forEach(el => {
          const t = (el.textContent || '').trim();
          if (t) tags.push(t);
        });
        if (tags.length === 0 && stateScript) {
          const tagRe = /"name":"([^"\\\\]+)","type":"topic"/g;
          let tm;
          while ((tm = tagRe.exec(stateScript)) !== null) {
            tags.push(jsonDecode(tm[1]));
          }
        }

        return { loginWall, notFound, title, desc, author, likes, collects, comments, tags };
      })()
    `);

    if (!data || typeof data !== 'object') {
      throw new EmptyResultError('xiaohongshu/note', 'Unexpected evaluate response');
    }

    if ((data as any).loginWall) {
      throw new AuthRequiredError('www.xiaohongshu.com', 'Note content requires login');
    }

    if ((data as any).notFound) {
      throw new EmptyResultError('xiaohongshu/note', `Note ${noteId} not found or unavailable — it may have been deleted or restricted`);
    }

    const d = data as any;
    // XHS renders placeholder text like "赞"/"收藏"/"评论" when count is 0;
    // normalize to '0' unless the value looks numeric.
    const numOrZero = (v: string) => /^\d+/.test(v) ? v : '0';
    const rows = [
      { field: 'title', value: d.title || '' },
      { field: 'author', value: d.author || '' },
      { field: 'content', value: d.desc || '' },
      { field: 'likes', value: numOrZero(d.likes || '') },
      { field: 'collects', value: numOrZero(d.collects || '') },
      { field: 'comments', value: numOrZero(d.comments || '') },
    ];

    if (d.tags?.length) {
      rows.push({ field: 'tags', value: d.tags.join(', ') });
    }

    return rows;
  },
});
