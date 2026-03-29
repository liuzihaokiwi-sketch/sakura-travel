import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";

export const dynamic = "force-dynamic";

const client = new Anthropic();

// ─── 系统提示 ─────────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `你是一个旅行内容库管理助手，负责帮助管理员通过自然语言管理酒店（hotel）、餐厅（restaurant）和景点/活动（poi）的数据。

你的能力：
1. **查询**：搜索、筛选、列出实体
2. **新建**：创建新的酒店/餐厅/景点
3. **修改**：更新某个实体的字段（名称、评分、状态、价格等）
4. **删除**：停用某个实体（软删除）
5. **调权重**：调整 editorial_boost（-8 到 +8）

实体结构：
- 通用字段：name_zh（中文名）、name_en（英文名）、city_code（城市）、area_name（区域）、data_tier（S/A/B）、is_active（是否启用）
- 酒店额外：hotel_type、star_rating、price_tier（budget/mid/premium/luxury）、typical_price_min_jpy
- 餐厅额外：cuisine_type、michelin_star、tabelog_score、price_range_min_jpy、price_range_max_jpy、requires_reservation
- 景点额外：poi_category、typical_duration_min、admission_fee_jpy、admission_free、google_rating、requires_advance_booking

城市代码：tokyo/osaka/kyoto/sapporo/fukuoka/naha/hakone/nikko

**响应格式**（必须严格返回 JSON）：
{
  "reply": "给管理员的自然语言回复（中文，简洁友好）",
  "action": null 或以下之一：
    {
      "type": "search",
      "params": { "entity_type": "hotel|restaurant|poi", "q": "搜索词", "city_code": "...", "data_tier": "..." }
    }
    {
      "type": "create",
      "entity_type": "hotel|restaurant|poi",
      "data": { ...字段 }
    }
    {
      "type": "update",
      "entity_id": "uuid",
      "data": { ...要修改的字段 }
    }
    {
      "type": "delete",
      "entity_id": "uuid"
    }
    {
      "type": "boost",
      "entity_id": "uuid",
      "editorial_boost": -8到8的整数,
      "score_profile": "general"
    }
    {
      "type": "confirm_needed",
      "description": "需要用户确认的操作描述"
    }
}

规则：
- 删除、停用操作必须先设 action.type = "confirm_needed"，等用户确认后再执行
- 如果用户说的是模糊查询（"找一下大阪的酒店"），用 search action
- 如果用户说的是具体修改但没提供 entity_id，先说明需要先搜索确认，再修改
- 如果信息不完整（比如新建但没给城市），在 reply 里追问，action 设 null
- 回复要简短、口语化，像在帮忙的同事`;

// ─── Route Handler ────────────────────────────────────────────────────────────

export async function POST(req: NextRequest) {
  try {
    const { messages, context } = await req.json() as {
      messages: { role: "user" | "assistant"; content: string }[];
      context?: { activeTab?: string; currentFilter?: Record<string, string> };
    };

    if (!messages?.length) {
      return NextResponse.json({ error: "messages required" }, { status: 400 });
    }

    // 把 context 注入到最后一条 user 消息前
    const contextNote = context
      ? `[当前界面：${context.activeTab ?? "hotel"} 列表${
          context.currentFilter?.city_code ? `，城市筛选：${context.currentFilter.city_code}` : ""
        }]`
      : "";

    const enrichedMessages = messages.map((m, i) =>
      i === messages.length - 1 && m.role === "user" && contextNote
        ? { ...m, content: `${contextNote}\n${m.content}` }
        : m
    );

    const response = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 1024,
      system: SYSTEM_PROMPT,
      messages: enrichedMessages,
    });

    const raw = response.content[0].type === "text" ? response.content[0].text : "";

    // 尝试解析 JSON，失败则包装成纯 reply
    let parsed: { reply: string; action: unknown };
    try {
      // Claude 有时会把 JSON 包在 ```json ``` 里
      const jsonMatch = raw.match(/```json\s*([\s\S]*?)```/) || raw.match(/(\{[\s\S]*\})/);
      const jsonStr = jsonMatch ? jsonMatch[1] : raw;
      parsed = JSON.parse(jsonStr);
    } catch {
      parsed = { reply: raw, action: null };
    }

    return NextResponse.json(parsed);
  } catch (e: any) {
    console.error("[catalog/chat]", e);
    return NextResponse.json({ error: e.message ?? "AI 服务异常" }, { status: 500 });
  }
}
