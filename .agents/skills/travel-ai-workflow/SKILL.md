---
name: travel-ai-workflow
description: Entry router for any task inside the travel-ai repo. Use first to classify the workstream (content/research, system rendering, visual production, marketing), pick the matching specialized skill, and read the smallest current handoff. Triggers - travel-ai, kansai, italy, handbook, 手账, 工作线.
---

# Travel AI Workflow

This skill is a thin trigger. The routing table, rules, and rituals live in the repo — do not duplicate them here.

1. Read `AGENTS.md` (repo root): red lines, routing table, validators.
2. Read `_tmp/handoff/CURRENT_README.md`: pick exactly one workstream and one `CURRENT_*` breakpoint.
3. Activate the one specialized skill named by the workstream (travel-ai-research / travel-ai-content-assembly / travel-ai-data-collection / handbook-system-rendering / handbook-visual-production / handbook-image-assets / travel-ai-marketing).
4. Work one slice, validate, land the plane (收尾仪式 in the global workflow layer).

Read `references/task-map.md` only if the task does not clearly match a workstream. Read `references/tools.md` only when no specialized skill has the needed command.
