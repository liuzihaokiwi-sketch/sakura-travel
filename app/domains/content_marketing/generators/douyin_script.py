"""
douyin_script.py — 抖音视频脚本生成器

输出结构：开头hook（0-3s）+ 主体内容 + 结尾CTA
总视频时长控制在 60-90 秒。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from app.domains.content_marketing.generator_base import ContentGenerator, ContentOutput


@dataclass
class ScriptSegment:
    """视频脚本分段"""
    label: str          # 段落名称（hook/内容1/.../cta）
    duration_sec: int   # 预计时长（秒）
    text: str           # 口播文案
    visuals: str = ""   # 镜头建议


@dataclass
class DouyinScript:
    """完整视频脚本"""
    title: str
    total_duration: int
    segments: list[ScriptSegment] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    cover_suggestion: str = ""

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", f"", f"**总时长：{self.total_duration}秒**", ""]
        for seg in self.segments:
            lines.append(f"## [{seg.label}] {seg.duration_sec}秒")
            lines.append(f"**口播：** {seg.text}")
            if seg.visuals:
                lines.append(f"**镜头：** {seg.visuals}")
            lines.append("")
        if self.hashtags:
            lines.append("**话题标签：** " + " ".join(f"#{t}" for t in self.hashtags))
        if self.cover_suggestion:
            lines.append(f"**封面建议：** {self.cover_suggestion}")
        return "\n".join(lines)


_DOUYIN_SYSTEM_PROMPT = (
    "你是一位日本旅行抖音博主，擅长写抓眼球的短视频脚本。"
    "开头3秒必须有强烈hook（悬念/冲突/惊喜）。"
    "口播节奏快，每句话简短有力，适合快速剪辑。"
    "有具体数字和细节，不说废话。"
)


def _build_douyin_prompt(topic: dict[str, Any], context: dict[str, Any]) -> str:
    template = topic.get("template", "city_guide")
    circle = context.get("circle_name", "关西")
    city = context.get("city", circle)
    days = context.get("days", 7)

    hook_examples = {
        "avoid_traps": f"去{city}千万别犯这{context.get('n', 5)}个错，踩一个就毁了整趟旅行",
        "food_ranking": f"这家{context.get('food_type', '拉面')}排队1小时，当地人说不值——但我不同意",
        "city_guide": f"{days}天{circle}，我帮你把所有坑踩完了",
        "budget_breakdown": f"{days}天{circle}花了多少钱？真实账单给你看",
        "seasonal_special": f"2026年{city}赏樱，这个时间去是错的",
        "comparison": f"{context.get('area_a', 'A区')} vs {context.get('area_b', 'B区')}，99%的人选错了",
    }
    hook = hook_examples.get(template, f"去{city}之前，你必须知道这些")

    return f"""帮我写一个抖音旅行视频脚本，关于{circle}旅行。

【视频主题】{hook}
【视频要求】
- 总时长：60-90秒
- 分段格式：[开头hook/内容段1/内容段2.../结尾CTA]
- 每段标注预计时长（秒）
- 口播文案 + 镜头建议

【上下文数据】
目的地：{circle}
天数：{days}天
选题类型：{template}

【输出格式（严格遵守）】
【视频标题】（20字内，有冲击力）
【封面建议】（一句话说明封面要拍什么）

【片段1-开头hook】时长：3秒
口播：...
镜头：...

【片段2-主体】时长：XX秒
口播：...
镜头：...

（根据内容继续分段，主体2-4段）

【片段N-结尾CTA】时长：5秒
口播：...
镜头：...

【话题标签】8-10个
【总时长】XX秒
"""


def _parse_douyin_output(raw: str) -> DouyinScript:
    """从 LLM 输出解析结构化脚本"""
    lines = raw.splitlines()
    title = ""
    cover = ""
    hashtags: list[str] = []
    total_dur = 0
    segments: list[ScriptSegment] = []

    current_label = ""
    current_dur = 0
    current_text_lines: list[str] = []
    current_visuals = ""

    def flush_segment():
        nonlocal current_label, current_dur, current_text_lines, current_visuals
        if current_label and current_text_lines:
            segments.append(ScriptSegment(
                label=current_label,
                duration_sec=current_dur,
                text="\n".join(current_text_lines).strip(),
                visuals=current_visuals.strip(),
            ))
        current_label = ""
        current_dur = 0
        current_text_lines = []
        current_visuals = ""

    import re

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("【视频标题】"):
            title = stripped[len("【视频标题】"):].strip()
        elif stripped.startswith("【封面建议】"):
            cover = stripped[len("【封面建议】"):].strip()
        elif stripped.startswith("【话题标签】"):
            raw_tags = stripped[len("【话题标签】"):].strip()
            hashtags = [t.strip().lstrip("#") for t in raw_tags.split() if t.strip()]
        elif stripped.startswith("【总时长】"):
            m = re.search(r"(\d+)", stripped)
            if m:
                total_dur = int(m.group(1))
        elif stripped.startswith("【片段"):
            flush_segment()
            # 解析 label 和时长
            m_label = re.search(r"【片段\d+-(.+?)】", stripped)
            m_dur = re.search(r"时长[：:]\s*(\d+)", stripped)
            current_label = m_label.group(1) if m_label else stripped
            current_dur = int(m_dur.group(1)) if m_dur else 0
        elif stripped.startswith("口播[：:]"):
            current_text_lines.append(stripped.split("：", 1)[-1].strip())
        elif stripped.lower().startswith("口播") and "：" in stripped:
            current_text_lines.append(stripped.split("：", 1)[-1].strip())
        elif stripped.lower().startswith("镜头") and "：" in stripped:
            current_visuals = stripped.split("：", 1)[-1].strip()
        elif current_label and stripped and not stripped.startswith("【"):
            current_text_lines.append(stripped)

    flush_segment()

    return DouyinScript(
        title=title,
        total_duration=total_dur or sum(s.duration_sec for s in segments),
        segments=segments,
        hashtags=hashtags,
        cover_suggestion=cover,
    )


class DouyinScriptGenerator(ContentGenerator):
    """
    抖音视频脚本生成器

    Usage::

        gen = DouyinScriptGenerator()
        out = gen.generate(
            topic={"template": "avoid_traps"},
            context={"city": "大阪", "n": 5}
        )
        # out.body 包含完整 Markdown 格式脚本
    """

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None, base_url: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("AI_BASE_URL", "https://api.openai.com/v1")

    def _call_llm(self, prompt: str) -> str:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise ImportError("需要安装 openai 包：pip install openai")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _DOUYIN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=1500,
        )
        return resp.choices[0].message.content or ""

    def generate(self, topic: dict[str, Any], context: dict[str, Any]) -> ContentOutput:
        prompt = _build_douyin_prompt(topic, context)
        raw = self._call_llm(prompt)
        script = _parse_douyin_output(raw)

        return ContentOutput(
            title=script.title,
            body=script.to_markdown(),
            image_hints=[script.cover_suggestion] if script.cover_suggestion else [],
            hashtags=script.hashtags,
            cta_text="想要完整行程？主页查看 / 私信获取",
        )
