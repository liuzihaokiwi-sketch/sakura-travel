---
name: travel-ai-marketing
description: Marketing and operations content workflow for the D:/projects/projects/travel-ai repository. Use when Codex works on Xiaohongshu or Douyin topics, viral note analysis, marketing copy, customer-service content, content calendars, marketing/japan/kansai assets, competitor notes, or render/marketing visual draft ownership.
---

# Travel AI Marketing

Use this skill for acquisition,运营内容, viral references, and customer-facing copy outside the handbook product itself.

## Boundary

- `marketing/` stores text strategy, topics,素材库,爆款参考, account notes, and publish records.
- `render/marketing/` stores visual drafts, covers, layouts, and rendered marketing assets.
- `render/references/` stores visual references.
- Product research evidence stays in `research/`; product conclusions stay with the formal object.

Do not move brand PNG/PDF/DOCX, map references, page-type samples, or visual source files into `marketing/`.

## Minimal Reading

```text
marketing/目录说明.md
marketing/strategy.md
marketing/templates.md
marketing/japan/kansai/素材库.md
marketing/japan/kansai/爆款参考.md
docs/操作SOP/上线后/内容运营客服.md
docs/操作SOP/opencli使用.md
```

For customer-service tasks, also read:

```text
docs/项目核心/业务流.md
docs/操作SOP/上线后/客服应对.md
```

## Workflow

1. Identify whether the task is topic mining, copywriting, account strategy, customer service, or visual draft ownership.
2. Pull product truth from `docs/项目核心/项目定位.md` and the relevant Kansai/product object; do not invent promises.
3. Use Xiaohongshu/opencli for viral examples when needed:
   - Search broad and specific keywords.
   - Read note details before judging.
   - Prefer收藏/长期参考价值 over raw likes.
4. Save reusable findings:
   - Topic hooks and local insights: `marketing/japan/kansai/素材库.md`
   - Viral structures and examples: `marketing/japan/kansai/爆款参考.md`
5. Put visual work under `render/marketing/{campaign_id}/`, with source notes if assets are used.

## Copy Rules

Anchor public copy to:

```text
一本为你写好的旅行手账
旅行时带着走，旅行后留作回忆
```

Do not describe the product as a generic攻略生成器, OTA, tour group, SaaS tool, or free AI itinerary.

## opencli Rules

Run `note` and `download` serially, use full URLs with `xsec_token`, and do not put downloaded media directly into `web/public`.
