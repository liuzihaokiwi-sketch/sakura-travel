#!/usr/bin/env python3
"""
generate_marketing_content.py — 营销内容批量生成 CLI

Usage::

    # 生成3篇关西小红书图文（美食排行选题）
    python scripts/generate_marketing_content.py --platform xhs --count 3 --topic food_ranking --circle kansai

    # 抖音脚本，自动建议选题
    python scripts/generate_marketing_content.py --platform douyin --suggest --circle hokkaido

    # 指定城市和天数
    python scripts/generate_marketing_content.py --platform xhs --topic city_guide --circle kansai --days 7 --city 京都

输出到 output/marketing/YYYYMMDD/ 目录，每篇一个 markdown 文件。
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

# 确保项目根目录在 path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domains.content_marketing.generators.douyin_script import DouyinScriptGenerator
from app.domains.content_marketing.generators.xiaohongshu_post import XiaohongshuPostGenerator
from app.domains.content_marketing.topic_pool import load_topics, suggest_topics

# 城市圈展示名
_CIRCLE_NAMES: dict[str, str] = {
    "kansai": "关西",
    "kanto": "关东",
    "hokkaido": "北海道",
    "guangfu": "广府",
    "xinjiang": "北疆",
}

# 各圈代表城市（默认值）
_CIRCLE_CITIES: dict[str, str] = {
    "kansai": "京都/大阪",
    "kanto": "东京",
    "hokkaido": "札幌",
    "guangfu": "广州",
    "xinjiang": "乌鲁木齐",
}


def build_context(args: argparse.Namespace, topic: dict) -> dict:
    circle_name = _CIRCLE_NAMES.get(args.circle, args.circle)
    city = args.city or _CIRCLE_CITIES.get(args.circle, circle_name)
    return {
        "circle_name": circle_name,
        "city": city,
        "days": args.days,
        "n": 5,
        "food_type": "拉面",
        "budget_level": "mid",
        "year": datetime.date.today().year,
        "season_type": "sakura" if datetime.date.today().month in (3, 4) else "koyo",
        "area_a": "市中心",
        "area_b": "郊区",
    }


def save_output(content, filename: str, output_dir: Path) -> Path:
    """保存到 markdown 文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename

    lines = [
        f"# {content.title}",
        "",
        content.body,
        "",
        "---",
        "",
        f"**CTA：** {content.cta_text}",
        "",
    ]
    if content.hashtags:
        lines.append("**话题标签：** " + " ".join(f"#{t}" for t in content.hashtags))
        lines.append("")
    if content.image_hints:
        lines.append("**配图建议：**")
        for hint in content.image_hints:
            lines.append(f"- {hint}")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="营销内容批量生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--platform", choices=["xhs", "douyin", "wechat"], default="xhs",
                        help="目标平台（xhs=小红书，douyin=抖音，wechat=公众号）")
    parser.add_argument("--count", type=int, default=1, help="生成数量")
    parser.add_argument("--topic", default=None,
                        help="选题模板：city_guide/food_ranking/budget_breakdown/seasonal_special/avoid_traps/comparison")
    parser.add_argument("--circle", default="kansai",
                        choices=list(_CIRCLE_NAMES.keys()),
                        help="目标城市圈")
    parser.add_argument("--city", default=None, help="具体城市（覆盖城市圈默认值）")
    parser.add_argument("--days", type=int, default=7, help="旅行天数")
    parser.add_argument("--suggest", action="store_true", help="自动建议选题（忽略 --topic）")
    parser.add_argument("--output-dir", default="output/marketing", help="输出目录")
    parser.add_argument("--dry-run", action="store_true", help="不实际调用 LLM，仅显示参数")

    args = parser.parse_args()

    # 准备输出目录
    date_str = datetime.date.today().strftime("%Y%m%d")
    output_dir = Path(args.output_dir) / date_str

    # 选题列表
    if args.suggest:
        topics = suggest_topics(platform=args.platform, limit=args.count)
        print(f"🤖 自动建议 {len(topics)} 个选题：")
        for t in topics:
            print(f"  [{t['score']:.1f}] {t['id']} — {t.get('reason', '')}")
    else:
        all_topics = load_topics()
        if args.topic:
            topics = [t for t in all_topics if t.get("template") == args.topic or t.get("id") == args.topic]
            if not topics:
                print(f"❌ 未找到选题：{args.topic}，可用：{list({t['template'] for t in all_topics})}")
                sys.exit(1)
            # 重复到满足 count
            topics = (topics * ((args.count // len(topics)) + 1))[:args.count]
        else:
            topics = all_topics[:args.count]

    # 选择生成器
    platform_label = {"xhs": "小红书", "douyin": "抖音", "wechat": "公众号"}[args.platform]
    print(f"\n📝 生成 {len(topics)} 篇 {platform_label} 内容 → {output_dir}\n")

    if args.dry_run:
        print("⚠️  dry-run 模式，不调用 LLM")
        for i, t in enumerate(topics):
            ctx = build_context(args, t)
            print(f"  [{i+1}] 选题={t.get('template')} 上下文={ctx}")
        return

    if args.platform == "xhs":
        generator = XiaohongshuPostGenerator()
    elif args.platform == "douyin":
        generator = DouyinScriptGenerator()
    else:
        from app.domains.content_marketing.generators.wechat_article import WechatArticleGenerator
        generator = WechatArticleGenerator()

    generated = []
    for i, topic in enumerate(topics):
        ctx = build_context(args, topic)
        print(f"  [{i+1}/{len(topics)}] 生成中：{topic.get('id', topic.get('template', '未知'))} ...")
        try:
            output = generator.generate(topic, ctx)
            ts = datetime.datetime.now().strftime("%H%M%S")
            filename = f"{args.platform}_{topic.get('template', 'content')}_{i+1:02d}_{ts}.md"
            saved = save_output(output, filename, output_dir)
            print(f"    ✅ 已保存：{saved}")
            generated.append(saved)
        except Exception as e:
            print(f"    ❌ 生成失败：{e}")

    print(f"\n🎉 完成！共生成 {len(generated)} 篇，输出目录：{output_dir.resolve()}")


if __name__ == "__main__":
    main()
