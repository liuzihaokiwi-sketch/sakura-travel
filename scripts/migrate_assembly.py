"""
批量迁移模板 assembly 字段：旧 role/priority/fatigue → 新 phase/best_pace。
同时补缺失的 slot 字段（area/duration_min）和 day_mood。
"""
import json
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "kansai"

# ── 每个模板的新 assembly 值（逐个思考后确定）──────────────────────────

NEW_ASSEMBLY: dict[str, dict] = {
    # === 城崎 ===
    "kinosaki_2day": {"phase": "sightseeing", "best_pace": "relaxed", "span_days": 2},

    # === 神户 ===
    "arima_onsen_2day": {"phase": "sightseeing", "best_pace": "relaxed", "span_days": 2},
    # 姬路+神户：景点密集（姬路城+好古园+北野+港+神户牛），紧凑才能全走完
    "himeji_kobe_day": {"phase": "sightseeing", "best_pace": "compact"},
    "kobe_day": {"phase": "sightseeing", "best_pace": "standard"},

    # === 高野山 ===
    "koyasan_2day": {"phase": "sightseeing", "best_pace": "relaxed", "span_days": 2},

    # === 京都 ===
    # 岚山：竹林+天龙寺+渡月桥+常寂光寺+...景点密集，紧凑体验最丰富
    "arashiyama_day": {"phase": "sightseeing", "best_pace": "compact"},
    # 岚山红叶：竹林+天龙寺+常寂光寺+二尊院+祇王寺三寺连走，高强度
    "arashiyama_koyo_day": {"phase": "sightseeing", "best_pace": "compact"},
    "arashiyama_onsen_stay": {"phase": "sightseeing", "best_pace": "relaxed", "span_days": 2},
    "arashiyama_sakura_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 到达日
    "kyoto_arrival_day": {"phase": "arrival", "best_pace": "relaxed"},
    # 人群专属日
    "kyoto_audience_couple_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    "kyoto_audience_friends_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 醍醐寺樱花：醍醐寺本身3小时+随心院+伏见十石舟，标准节奏
    "daigoji_sakura_day": {"phase": "sightseeing", "best_pace": "standard"},
    "kyoto_departure_half": {"phase": "departure", "best_pace": "relaxed"},
    # 伏见清酒：悠闲为主，酒蔵巡り本身就是慢体验
    "fushimi_sake_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    # 祇园祭山鉾巡行：祭典日，时间被祭典绑定，无法调整
    "gion_matsuri_yamaboko_day": {"phase": "sightseeing", "best_pace": "locked"},
    # 祇园祭宵山：傍晚开始，白天自由+晚上祭典，标准节奏
    "gion_matsuri_yoiyama_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 东山：清水寺→三年坂→高台寺→八坂→祇园，景点密集路线连贯，紧凑最佳
    "higashiyama_day": {"phase": "sightseeing", "best_pace": "compact"},
    "higashiyama_koyo_day": {"phase": "sightseeing", "best_pace": "compact"},
    # 金阁寺北野：金阁寺+龙安寺+仁和寺+北野天满宫，景点间有距离但不算密集
    "kinkaku_kitano_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 贵船�的花马：爬山+温泉，体力要求高但景点不多，标准节奏（不用赶）
    "kurama_kibune_day": {"phase": "sightseeing", "best_pace": "standard"},
    "kyoto_ajisai_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 手工艺日：体验型活动节奏慢
    "kyoto_craft_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    # 夜间特别公开：白天轻松+晚上重头戏
    "kyoto_night_tokubetsu": {"phase": "sightseeing", "best_pace": "standard"},
    # 铁道博物馆+水族馆：亲子专属
    "kyoto_railway_aquarium_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 恢复日
    "kyoto_recovery_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    "kyoto_winter_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 圆山夜樱：下午开始+夜樱，标准节奏
    "maruyama_yozakura_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 二条城+御所：两个大景点+周边，标准
    "nijo_gosho_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 任天堂博物馆：需预约，半天在馆内
    "nintendo_museum_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 大原：远离市区的山里体验，慢节奏才有意义
    "ohara_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    # 冈崎：银阁寺+哲学之道+南禅寺+平安神宫，路线顺畅景点适中
    "okazaki_day": {"phase": "sightseeing", "best_pace": "standard"},
    "okazaki_koyo_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 哲学之道樱花：樱花隧道本身要慢走才有意义
    "philosopher_sakura_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 嵯峨野深度：竹林深处+化野念仏寺+�的近辺，远+少人，悠闲
    "sagano_deep_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    # 嵯峨野小火车：小火车+保津川+岚山，紧凑才能全走完
    "sagano_torokko_day": {"phase": "sightseeing", "best_pace": "compact"},
    # 高雄红叶：400级石阶+三寺巡游，高强度但景点不算多，标准
    "takao_koyo_day": {"phase": "sightseeing", "best_pace": "standard"},
    "takao_onsen_2day": {"phase": "sightseeing", "best_pace": "relaxed", "span_days": 2},
    "teamlab_kyoto_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 换城
    "transfer_kyoto_to_osaka": {"phase": "transfer", "best_pace": "standard"},

    # === 奈良 ===
    "nara_day": {"phase": "sightseeing", "best_pace": "standard"},
    "nara_luxury_stay": {"phase": "sightseeing", "best_pace": "relaxed", "span_days": 2},

    # === 大阪 ===
    "arrival_day": {"phase": "arrival", "best_pace": "relaxed"},
    "audience_couple_day": {"phase": "sightseeing", "best_pace": "standard"},
    "audience_default_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    "audience_family_day": {"phase": "sightseeing", "best_pace": "standard"},
    "audience_friends_day": {"phase": "sightseeing", "best_pace": "standard"},
    # 大阪核心日：大阪城+道顿堀+心斎桥+通天閣，景点密集
    "core_day": {"phase": "sightseeing", "best_pace": "compact"},
    # 温泉深度：空庭温泉等，悠闲
    "deep_dive_onsen": {"phase": "sightseeing", "best_pace": "relaxed"},
    "deep_dive_urban": {"phase": "sightseeing", "best_pace": "standard"},
    "departure_half": {"phase": "departure", "best_pace": "relaxed"},
    "hanabi_day": {"phase": "sightseeing", "best_pace": "locked"},
    # 泉佐野离开：关西机场附近半日
    "izumisano_departure": {"phase": "departure", "best_pace": "relaxed"},
    # 海游馆天保山：海游馆本身3-4小时+天保山，标准
    "kaiyukan_tempozan_day": {"phase": "sightseeing", "best_pace": "standard"},
    "minoo_koyo_day": {"phase": "sightseeing", "best_pace": "standard"},
    # USJ：全天在园内，强度固定无法降级
    "module_usj": {"phase": "sightseeing", "best_pace": "locked"},
    "nakanoshima_kitahama_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    "osaka_castle_sakura_day": {"phase": "sightseeing", "best_pace": "standard"},
    "recovery_day": {"phase": "sightseeing", "best_pace": "relaxed"},
    # 天神祭：祭典日，时间被祭典绑定
    "tenjin_matsuri_day": {"phase": "sightseeing", "best_pace": "locked"},
    "transfer_osaka_to_kyoto": {"phase": "transfer", "best_pace": "standard"},

    # === 宇治 ===
    # 宇治："慢"是灵魂
    "uji_day": {"phase": "sightseeing", "best_pace": "relaxed"},
}

# ── 缺失 day_mood 补充 ──────────────────────────────────────────────

DAY_MOOD_FIXES: dict[str, str] = {
    "kyoto_railway_aquarium_day": "day_mood: 童心与好奇。",
    "audience_couple_day": "day_mood: 甜蜜与发现。",
    "audience_family_day": "day_mood: 欢笑与安心。",
    "deep_dive_onsen": "day_mood: 彻底放空。",
    "departure_half": "day_mood: 余韵与告别。",
    "module_usj": "day_mood: 全力释放。",
    "osaka_castle_sakura_day": "day_mood: 壮阔与春色。",
    "recovery_day": "day_mood: 充电与闲逛。",
    "tenjin_matsuri_day": "day_mood: 热狂与夏夜。",
}


def migrate_file(path: Path) -> bool:
    """迁移单个模板文件，返回是否有改动。"""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    tid = data.get("template_id", path.stem)
    changed = False

    # 1. 替换 assembly
    if tid in NEW_ASSEMBLY:
        old_asm = data.get("assembly", {})
        new_asm = NEW_ASSEMBLY[tid]
        if old_asm != new_asm:
            data["assembly"] = new_asm
            changed = True

    # 2. 补 day_mood
    if tid in DAY_MOOD_FIXES:
        desc = data.get("description", "")
        if "day_mood" not in desc:
            data["description"] = DAY_MOOD_FIXES[tid] + desc
            changed = True

    if changed:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return changed


def main() -> None:
    migrated = 0
    total = 0
    missing = []
    for city_dir in sorted(CONTENT_DIR.iterdir()):
        days_dir = city_dir / "days"
        if not days_dir.is_dir():
            continue
        for f in sorted(days_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            total += 1
            tid = json.loads(f.read_text(encoding="utf-8")).get("template_id", f.stem)
            if tid not in NEW_ASSEMBLY:
                missing.append(tid)
                continue
            if migrate_file(f):
                migrated += 1
                print(f"  ✓ {f.relative_to(CONTENT_DIR)}")

    print(f"\n迁移完成：{migrated}/{total} 个文件有改动")
    if missing:
        print(f"\n⚠ 未覆盖的模板（需手动添加到 NEW_ASSEMBLY）：")
        for m in missing:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
