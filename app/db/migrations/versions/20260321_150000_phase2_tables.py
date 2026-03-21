"""phase2_tables: entity_alternatives, candidate_pool_cache, user_entity_feedback,
city_monthly_context, entity_time_window_scores, seasonal_events, transit_matrix

Revision ID: 20260321_150000
Revises: 20260321_140000
Create Date: 2026-03-21 15:00:00

覆盖任务:
- T10: entity_alternatives         — 自助微调候选池核心表
- T11: candidate_pool_cache        — 方案级候选缓存
- T17: user_entity_feedback        — 旅行后用户验证反馈
- T18: city_monthly_context        — P0 城市 × 12 月季节上下文
- T19: entity_time_window_scores   — 实体六维交叉评分
- T20: seasonal_events             — P0 城市全年活动/花期
- T21: transit_matrix              — 区域间交通矩阵
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260321_150000"
down_revision = "20260321_140000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── T10: entity_alternatives ────────────────────────────────────────────
    # 每个实体 slot（按城市+类别+标签）预计算 3-5 个替换候选
    op.create_table(
        "entity_alternatives",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("source_entity_id", UUID(as_uuid=True), nullable=False, comment="被替换的原实体 ID"),
        sa.Column("alt_entity_id", UUID(as_uuid=True), nullable=False, comment="候选替换实体 ID"),
        sa.Column("city_code", sa.String(30), nullable=False),
        sa.Column("slot_type", sa.String(20), nullable=False, comment="景点/餐厅/住宿/交通枢纽"),
        sa.Column("similarity_score", sa.Numeric(4, 3), nullable=False, comment="0-1，综合相似度"),
        sa.Column("swap_safe", sa.Boolean, nullable=False, default=True, comment="通勤/餐饮时段/体力综合校验结果"),
        sa.Column("distance_km", sa.Numeric(6, 2), comment="与原实体距离"),
        sa.Column("shared_tags", JSONB, comment="['romantic_spot','photo_friendly',...]"),
        sa.Column("diff_tags", JSONB, comment="候选独有标签"),
        sa.Column("reason_zh", sa.Text, comment="推荐理由（中文，用于前端展示）"),
        sa.Column("rank", sa.SmallInteger, nullable=False, default=1, comment="候选排名 1-5"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), comment="缓存有效期，NULL 表示永久"),
    )
    op.create_index("ix_entity_alts_source", "entity_alternatives", ["source_entity_id"])
    op.create_index("ix_entity_alts_city_slot", "entity_alternatives", ["city_code", "slot_type"])
    op.create_index(
        "ix_entity_alts_source_rank",
        "entity_alternatives",
        ["source_entity_id", "rank"],
    )

    # ── T11: candidate_pool_cache ───────────────────────────────────────────
    # 方案级别的候选缓存（plan_id + slot_index → 候选列表快照）
    op.create_table(
        "candidate_pool_cache",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("plan_id", UUID(as_uuid=True), nullable=False, comment="行程方案 ID"),
        sa.Column("day_number", sa.SmallInteger, nullable=False),
        sa.Column("slot_index", sa.SmallInteger, nullable=False, comment="当天第几个 slot（0-based）"),
        sa.Column("source_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("candidates", JSONB, nullable=False, comment="[{entity_id, name, score, reason_zh,...}, ...]"),
        sa.Column("constraint_summary", JSONB, comment="通勤约束、体力预算等汇总"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cpc_plan_day", "candidate_pool_cache", ["plan_id", "day_number"])
    op.create_index(
        "ix_cpc_plan_slot",
        "candidate_pool_cache",
        ["plan_id", "day_number", "slot_index"],
        unique=True,
    )

    # ── T17: user_entity_feedback ───────────────────────────────────────────
    # 旅行后回访用户对推荐实体的验证反馈
    op.create_table(
        "user_entity_feedback",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False, comment="来源订单 ID"),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False, comment="被评价实体 ID"),
        sa.Column("user_id", UUID(as_uuid=True), comment="匿名时为 NULL"),
        # 结构化评分
        sa.Column("visited", sa.Boolean, comment="是否实际去了"),
        sa.Column("rating", sa.SmallInteger, comment="1-5 星评分"),
        sa.Column("recommendation_match", sa.SmallInteger, comment="推荐与实际吻合度 1-5"),
        # 维度评分
        sa.Column("crowd_level_actual", sa.SmallInteger, comment="实际排队/人流 1-5"),
        sa.Column("food_quality_actual", sa.SmallInteger, comment="餐厅专用：食物评分 1-5"),
        sa.Column("photo_spot_quality", sa.SmallInteger, comment="拍摄效果 1-5"),
        # 文字反馈
        sa.Column("comment", sa.Text),
        sa.Column("tags_added", JSONB, comment="用户自行添加的标签"),
        sa.Column("verified", sa.Boolean, default=False, comment="已审核并入库"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_uef_entity", "user_entity_feedback", ["entity_id"])
    op.create_index("ix_uef_order", "user_entity_feedback", ["order_id"])
    op.create_index("ix_uef_verified", "user_entity_feedback", ["verified"])

    # ── T18: city_monthly_context ───────────────────────────────────────────
    # P0 城市 × 12 个月的季节上下文（用于生成时注入天气/花期/节假日警告）
    op.create_table(
        "city_monthly_context",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("city_code", sa.String(30), nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False, comment="1-12"),
        # 天气信息
        sa.Column("avg_temp_high_c", sa.Numeric(4, 1)),
        sa.Column("avg_temp_low_c", sa.Numeric(4, 1)),
        sa.Column("avg_rain_days", sa.SmallInteger, comment="月均降雨天数"),
        sa.Column("uv_index_avg", sa.SmallInteger),
        sa.Column("comfort_score", sa.SmallInteger, comment="综合舒适度 1-10"),
        # 旅行质量
        sa.Column("crowd_level", sa.SmallInteger, comment="人流指数 1-5（5=极拥挤）"),
        sa.Column("price_index", sa.SmallInteger, comment="物价/酒店价格指数 1-5"),
        sa.Column("recommended_for", JSONB, comment="['couple','family','solo','photography']"),
        # 描述文本
        sa.Column("season_label_zh", sa.String(20), comment="梅雨季/樱花季/红叶季等"),
        sa.Column("highlights_zh", JSONB, comment="['樱花全开','白川乡合掌造积雪']"),
        sa.Column("warnings_zh", JSONB, comment="['黄金周极度拥挤','梅雨需携带雨具']"),
        sa.Column("packing_tips_zh", JSONB),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_cmc_city_month",
        "city_monthly_context",
        ["city_code", "month"],
        unique=True,
    )

    # ── T19: entity_time_window_scores ──────────────────────────────────────
    # 实体六维交叉评分（月份×时段×人群×天气×工作日/节假日×热度趋势）
    op.create_table(
        "entity_time_window_scores",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False, comment="1-12，0=全年通用"),
        sa.Column("time_slot", sa.String(20), nullable=False,
                  comment="early_morning/morning/afternoon/evening/night"),
        sa.Column("day_type", sa.String(20), nullable=False, default="any",
                  comment="any/weekday/weekend/holiday"),
        sa.Column("weather_condition", sa.String(20), nullable=False, default="any",
                  comment="any/sunny/cloudy/rain/snow"),
        # 六维评分（1-10）
        sa.Column("crowd_score", sa.SmallInteger, comment="拥挤程度（10=最不拥挤）"),
        sa.Column("experience_score", sa.SmallInteger, comment="当前时段体验质量"),
        sa.Column("photo_score", sa.SmallInteger, comment="拍摄效果"),
        sa.Column("accessibility_score", sa.SmallInteger, comment="交通可达性"),
        sa.Column("value_score", sa.SmallInteger, comment="性价比"),
        sa.Column("overall_score", sa.Numeric(4, 2), comment="加权综合分"),
        sa.Column("visit_tips_zh", sa.Text, comment="当前时窗专属建议"),
        sa.Column("source", sa.String(20), default="manual", comment="manual/ai_computed/user_verified"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_etws_entity", "entity_time_window_scores", ["entity_id"])
    op.create_index(
        "ix_etws_entity_month_slot",
        "entity_time_window_scores",
        ["entity_id", "month", "time_slot"],
    )

    # ── T20: seasonal_events ─────────────────────────────────────────────────
    # P0 城市全年活动/花期（用于生成时的时间节点注入）
    op.create_table(
        "seasonal_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("city_code", sa.String(30), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False,
                  comment="bloom/festival/holiday/market/exhibition/sport"),
        sa.Column("name_zh", sa.String(100), nullable=False),
        sa.Column("name_ja", sa.String(100)),
        sa.Column("month_start", sa.SmallInteger, nullable=False, comment="通常开始月份"),
        sa.Column("month_end", sa.SmallInteger, nullable=False),
        sa.Column("day_start", sa.SmallInteger, comment="通常开始日（可NULL=月份粒度）"),
        sa.Column("day_end", sa.SmallInteger),
        sa.Column("peak_week", sa.SmallInteger, comment="高峰通常在哪周（1-5）"),
        sa.Column("location_hint_zh", sa.String(200), comment="代表观赏/参与地点"),
        sa.Column("related_entity_ids", JSONB, comment="关联实体 ID 列表"),
        sa.Column("description_zh", sa.Text),
        sa.Column("planning_tips_zh", sa.Text, comment="规划建议：提前预订/避开人流等"),
        sa.Column("photo_tips_zh", sa.Text),
        sa.Column("crowd_impact", sa.SmallInteger, comment="对所在城市人流影响 1-5"),
        sa.Column("price_impact", sa.SmallInteger, comment="对酒店价格影响 1-5"),
        sa.Column("is_annual", sa.Boolean, default=True, comment="是否每年固定"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_se_city_month", "seasonal_events", ["city_code", "month_start"])
    op.create_index("ix_se_type", "seasonal_events", ["event_type"])

    # ── T21: transit_matrix ──────────────────────────────────────────────────
    # 区域间交通矩阵（用于规划时的通勤约束检查和路线排序）
    op.create_table(
        "transit_matrix",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("city_code", sa.String(30), nullable=False),
        sa.Column("from_area", sa.String(50), nullable=False, comment="区域代码，如 ueno / shinjuku"),
        sa.Column("to_area", sa.String(50), nullable=False),
        sa.Column("transit_mode", sa.String(20), nullable=False,
                  comment="metro/bus/walk/taxi/shinkansen"),
        # 时间数据
        sa.Column("duration_min_avg", sa.SmallInteger, nullable=False, comment="平均时长（分钟）"),
        sa.Column("duration_min_peak", sa.SmallInteger, comment="高峰时长（分钟）"),
        sa.Column("duration_min_offpeak", sa.SmallInteger),
        # 费用
        sa.Column("cost_cny_approx", sa.Numeric(6, 1), comment="约折人民币"),
        sa.Column("cost_jpy_approx", sa.SmallInteger),
        # 便捷性
        sa.Column("transfer_count", sa.SmallInteger, default=0),
        sa.Column("accessibility", sa.SmallInteger, comment="无障碍程度 1-5"),
        sa.Column("recommended_mode", sa.Boolean, default=True, comment="是否为推荐方式"),
        sa.Column("route_hint_zh", sa.String(300), comment="关键路线说明"),
        sa.Column("source", sa.String(20), default="manual"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_tm_city_from_to",
        "transit_matrix",
        ["city_code", "from_area", "to_area"],
    )
    op.create_index("ix_tm_mode", "transit_matrix", ["transit_mode"])

    # ── plan_swap_logs（T14 自助微调操作日志）───────────────────────────────
    op.create_table(
        "plan_swap_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("plan_id", UUID(as_uuid=True), nullable=False),
        sa.Column("day_number", sa.SmallInteger, nullable=False),
        sa.Column("slot_index", sa.SmallInteger, nullable=False),
        sa.Column("old_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("new_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("time_slot", sa.String(20)),
        sa.Column("user_reason", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, default="applied",
                  comment="applied/reverted"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_psl_plan", "plan_swap_logs", ["plan_id"])
    op.create_index("ix_psl_plan_day", "plan_swap_logs", ["plan_id", "day_number"])

    # 为东京 P0 区域插入基础交通矩阵数据
    _seed_tokyo_transit(op)


def _seed_tokyo_transit(op) -> None:
    """东京主要区域间交通矩阵种子数据"""
    conn = op.get_bind()
    rows = [
        # (city, from_area, to_area, mode, avg_min, cost_jpy, transfers, route_hint)
        ("tokyo", "ueno", "asakusa", "metro", 8, 180, 1, "银座线 上野→浅草 直达"),
        ("tokyo", "ueno", "akihabara", "metro", 5, 180, 0, "JR山手线/京滨东北线 上野→秋叶原"),
        ("tokyo", "asakusa", "skytree", "walk", 15, 0, 0, "步行约1.2km，沿隅田川向南"),
        ("tokyo", "asakusa", "ginza", "metro", 18, 220, 1, "银座线 浅草→銀座"),
        ("tokyo", "shinjuku", "shibuya", "metro", 7, 180, 0, "JR山手线/副都心线 新宿→涩谷"),
        ("tokyo", "shinjuku", "harajuku", "metro", 5, 180, 0, "JR山手线 新宿→原宿"),
        ("tokyo", "shibuya", "harajuku", "walk", 10, 0, 0, "步行约800m，竹下通入口"),
        ("tokyo", "roppongi", "shibuya", "metro", 12, 200, 0, "日比谷线 六本木→惠比寿换乘JR"),
        ("tokyo", "akihabara", "ueno", "metro", 5, 180, 0, "JR山手线/京滨东北线 秋叶原→上野"),
        ("tokyo", "skytree", "asakusa", "walk", 15, 0, 0, "步行约1.2km，沿隅田川向北"),
        ("tokyo", "ginza", "tsukiji", "walk", 12, 0, 0, "步行约1km，筑地外市场"),
        ("tokyo", "harajuku", "shibuya", "walk", 10, 0, 0, "步行约800m，明治通り"),
        # 大阪主要区域
        ("osaka", "dotonbori", "shinsaibashi", "walk", 5, 0, 0, "步行约400m"),
        ("osaka", "shinsaibashi", "namba", "walk", 8, 0, 0, "步行约600m"),
        ("osaka", "namba", "tsutenkaku", "metro", 10, 230, 1, "御堂筋线→长堀鹤见緑地线 大国町"),
        ("osaka", "kuromon_market", "dotonbori", "walk", 12, 0, 0, "步行约900m"),
        ("osaka", "umeda", "dotonbori", "metro", 12, 230, 0, "御堂筋线 梅田→难波"),
        # 京都主要区域
        ("kyoto", "fushimi_inari", "gion", "metro", 25, 260, 1, "近铁京都线→市营地铁 烏丸御池换乘"),
        ("kyoto", "gion", "nishiki_market", "walk", 12, 0, 0, "步行约900m"),
        ("kyoto", "nishiki_market", "gion", "walk", 12, 0, 0, "步行约900m"),
        ("kyoto", "gion", "philosophers_path", "walk", 20, 0, 0, "步行约1.5km 或公交5分钟"),
        ("kyoto", "kinkakuji", "arashiyama", "bus", 30, 230, 0, "公交59号线"),
        ("kyoto", "arashiyama", "fushimi_inari", "train", 45, 310, 2, "嵯峨野线→奈良线"),
    ]

    for row in rows:
        city, from_a, to_a, mode, avg_min, cost_jpy, transfers, hint = row
        conn.execute(
            sa.text(
                """INSERT INTO transit_matrix
                   (city_code, from_area, to_area, transit_mode,
                    duration_min_avg, cost_jpy_approx, transfer_count,
                    route_hint_zh, recommended_mode)
                   VALUES (:city, :from_a, :to_a, :mode,
                           :avg_min, :cost_jpy, :transfers, :hint, true)"""
            ),
            {
                "city": city,
                "from_a": from_a,
                "to_a": to_a,
                "mode": mode,
                "avg_min": avg_min,
                "cost_jpy": cost_jpy,
                "transfers": transfers,
                "hint": hint,
            },
        )


def downgrade() -> None:
    op.drop_table("transit_matrix")
    op.drop_table("seasonal_events")
    op.drop_table("entity_time_window_scores")
    op.drop_table("city_monthly_context")
    op.drop_table("user_entity_feedback")
    op.drop_table("candidate_pool_cache")
    op.drop_table("entity_alternatives")
