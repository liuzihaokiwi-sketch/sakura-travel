"""四层架构新增表 (P1-L4)

Revision ID: 20260323_010000
Revises: 20260322_040000
Create Date: 2026-03-23 01:00:00.000000

新增表（共 14 张）：
  entity_alias               — 实体别名（L1 T1/T3）
  entity_field_provenance    — 字段溯源（L1 T10）
  entity_mapping_reviews     — 映射审核（L1）
  entity_temporal_profiles   — 实体时态配置（L1 T9）
  city_circles               — 城市圈定义（L2 T5）
  activity_clusters          — 活动簇（L2 T6）
  circle_entity_roles        — 圈内实体角色（L2 T7）
  hotel_strategy_presets     — 住宿策略预设（L2 T8）
  corridors                  — 路线走廊（L2 T14）
  corridor_alias_map         — 走廊别名（L2 T14）
  page_hero_registry         — 页面主图注册表（L3 T12）
  generation_decisions       — 生成决策记录（L3 T11）
  operator_overrides         — 运营干预（L4-01）
  live_risk_rules            — 实时风险规则（L4-03）
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260323_010000"
down_revision = "20260322_040000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. entity_alias ───────────────────────────────────────────────────────
    op.create_table(
        "entity_alias",
        sa.Column("alias_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alias_text", sa.String(200), nullable=False),
        sa.Column("alias_lang", sa.String(10), nullable=False, server_default="zh",
                  comment="zh / en / ja / ja-roman"),
        sa.Column("alias_type", sa.String(30), nullable=False, server_default="common",
                  comment="common / official / abbreviation / nickname"),
        sa.Column("normalized_text", sa.String(200), nullable=True,
                  comment="lowercase + strip spaces，供匹配用"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="1.0"),
        sa.Column("source", sa.String(50), nullable=True,
                  comment="editor / google / tabelog / ai_extract"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_entity_alias_entity_id", "entity_alias", ["entity_id"])
    op.create_index("ix_entity_alias_normalized", "entity_alias", ["normalized_text"])

    # ── 2. entity_field_provenance ────────────────────────────────────────────
    op.create_table(
        "entity_field_provenance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False,
                  comment="editor / google_api / tabelog / ai_extract / import"),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_stale", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("staleness_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_efp_entity_field", "entity_field_provenance", ["entity_id", "field_name"])

    # ── 3. entity_mapping_reviews ─────────────────────────────────────────────
    op.create_table(
        "entity_mapping_reviews",
        sa.Column("review_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_type", sa.String(30), nullable=False,
                  comment="alias_merge / entity_merge / data_correction / flag_stale"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending",
                  comment="pending / approved / rejected"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_emr_entity_id", "entity_mapping_reviews", ["entity_id"])
    op.create_index("ix_emr_status", "entity_mapping_reviews", ["status"])

    # ── 4. entity_temporal_profiles ──────────────────────────────────────────
    op.create_table(
        "entity_temporal_profiles",
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("closed_days", postgresql.ARRAY(sa.Integer), nullable=True,
                  comment="ISO weekday: 1=Mon, 7=Sun"),
        sa.Column("closed_dates", postgresql.ARRAY(sa.String(10)), nullable=True,
                  comment="YYYY-MM-DD 固定关闭日"),
        sa.Column("peak_months", postgresql.ARRAY(sa.Integer), nullable=True,
                  comment="月份列表 [1..12]"),
        sa.Column("crowd_level_by_month", postgresql.JSONB, nullable=True,
                  comment='{"1": 0.3, "4": 0.9, ...} 人流指数 0-1'),
        sa.Column("special_hours", postgresql.JSONB, nullable=True,
                  comment="特殊日期/节假日开放时间覆盖"),
        sa.Column("seasonal_notes_zh", sa.Text, nullable=True),
        sa.Column("seasonal_notes_en", sa.Text, nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_etp_entity_id", "entity_temporal_profiles", ["entity_id"])

    # ── 5. city_circles ───────────────────────────────────────────────────────
    op.create_table(
        "city_circles",
        sa.Column("circle_id", sa.String(50), primary_key=True,
                  comment="human-readable，如 kansai_v1"),
        sa.Column("name_zh", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=False),
        sa.Column("base_cities", postgresql.ARRAY(sa.String(50)), nullable=False,
                  comment="主城市列表，用于路线规划"),
        sa.Column("extension_cities", postgresql.ARRAY(sa.String(50)), nullable=True,
                  comment="可延伸城市"),
        sa.Column("anchor_city", sa.String(50), nullable=False,
                  comment="主锚定城市，用于 hotel 分配"),
        sa.Column("min_days", sa.Integer, nullable=False, server_default="3"),
        sa.Column("max_days", sa.Integer, nullable=False, server_default="14"),
        sa.Column("geo_bbox", postgresql.JSONB, nullable=True,
                  comment='{"lat_min":..,"lat_max":..,"lng_min":..,"lng_max":..}'),
        sa.Column("description_zh", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # ── 6. activity_clusters ──────────────────────────────────────────────────
    op.create_table(
        "activity_clusters",
        sa.Column("cluster_id", sa.String(80), primary_key=True),
        sa.Column("circle_id", sa.String(50), nullable=False),
        sa.Column("name_zh", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=False),
        sa.Column("tier", sa.String(2), nullable=False, server_default="A",
                  comment="S / A / B"),
        sa.Column("primary_corridor_id", sa.String(80), nullable=True),
        sa.Column("default_duration_hrs", sa.Numeric(4, 1), nullable=False, server_default="2.0"),
        sa.Column("capacity_units", sa.Integer, nullable=False, server_default="1"),
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("geo_center", postgresql.JSONB, nullable=True,
                  comment='{"lat": .., "lng": ..}'),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_ac_circle_id", "activity_clusters", ["circle_id"])
    op.create_index("ix_ac_tier", "activity_clusters", ["tier"])

    # ── 7. circle_entity_roles ────────────────────────────────────────────────
    op.create_table(
        "circle_entity_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("circle_id", sa.String(50), nullable=False),
        sa.Column("cluster_id", sa.String(80), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False,
                  comment="anchor / secondary / backup"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="50"),
        sa.Column("override_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_cer_circle_entity", "circle_entity_roles", ["circle_id", "entity_id"])
    op.create_index("ix_cer_cluster", "circle_entity_roles", ["cluster_id"])

    # ── 8. hotel_strategy_presets ─────────────────────────────────────────────
    op.create_table(
        "hotel_strategy_presets",
        sa.Column("preset_id", sa.String(80), primary_key=True),
        sa.Column("circle_id", sa.String(50), nullable=False),
        sa.Column("strategy_name_zh", sa.String(100), nullable=False),
        sa.Column("strategy_name_en", sa.String(100), nullable=False),
        sa.Column("base_cities_order", postgresql.ARRAY(sa.String(50)), nullable=False,
                  comment="住宿城市顺序"),
        sa.Column("min_days", sa.Integer, nullable=False, server_default="1"),
        sa.Column("max_days", sa.Integer, nullable=False, server_default="99"),
        sa.Column("segment_fit", postgresql.ARRAY(sa.String(30)), nullable=True,
                  comment="适合的用户画像，如 couple / family"),
        sa.Column("description_zh", sa.Text, nullable=True),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_hsp_circle_id", "hotel_strategy_presets", ["circle_id"])

    # ── 9. corridors ──────────────────────────────────────────────────────────
    op.create_table(
        "corridors",
        sa.Column("corridor_id", sa.String(80), primary_key=True),
        sa.Column("circle_id", sa.String(50), nullable=False),
        sa.Column("name_zh", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=False),
        sa.Column("area_codes", postgresql.ARRAY(sa.String(50)), nullable=True,
                  comment="覆盖的区域代码"),
        sa.Column("transit_type", sa.String(30), nullable=True,
                  comment="train / bus / walk / mix"),
        sa.Column("typical_duration_hrs", sa.Numeric(4, 1), nullable=True),
        sa.Column("geo_polyline", sa.Text, nullable=True,
                  comment="encoded polyline"),
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_corridors_circle_id", "corridors", ["circle_id"])

    # ── 10. corridor_alias_map ────────────────────────────────────────────────
    op.create_table(
        "corridor_alias_map",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("corridor_id", sa.String(80), nullable=False),
        sa.Column("alias_text", sa.String(200), nullable=False),
        sa.Column("alias_lang", sa.String(10), nullable=False, server_default="zh"),
        sa.Column("normalized_text", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_cam_corridor_id", "corridor_alias_map", ["corridor_id"])
    op.create_index("ix_cam_normalized", "corridor_alias_map", ["normalized_text"])

    # ── 11. page_hero_registry ────────────────────────────────────────────────
    op.create_table(
        "page_hero_registry",
        sa.Column("hero_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope_type", sa.String(30), nullable=False,
                  comment="entity / corridor / circle / city"),
        sa.Column("scope_id", sa.String(100), nullable=False),
        sa.Column("page_type", sa.String(50), nullable=True,
                  comment="限定用于哪种 page_type，null=通用"),
        sa.Column("image_url", sa.Text, nullable=False),
        sa.Column("image_alt_zh", sa.String(200), nullable=True),
        sa.Column("image_alt_en", sa.String(200), nullable=True),
        sa.Column("orientation", sa.String(20), nullable=False, server_default="landscape",
                  comment="landscape / portrait / square"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="50"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_phr_scope", "page_hero_registry", ["scope_type", "scope_id"])

    # ── 12. generation_decisions ──────────────────────────────────────────────
    op.create_table(
        "generation_decisions",
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True,
                  comment="关联 generation_runs.run_id"),
        sa.Column("step_name", sa.String(80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cluster_id", sa.String(80), nullable=True),
        sa.Column("decision_type", sa.String(30), nullable=False,
                  comment="include / exclude / swap / pin"),
        sa.Column("reason_code", sa.String(80), nullable=True),
        sa.Column("reason_detail", sa.Text, nullable=True),
        sa.Column("score_before", sa.Numeric(6, 3), nullable=True),
        sa.Column("score_after", sa.Numeric(6, 3), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_gd_run_id", "generation_decisions", ["run_id"])
    op.create_index("ix_gd_step", "generation_decisions", ["step_name"])

    # ── 13. operator_overrides ────────────────────────────────────────────────
    op.create_table(
        "operator_overrides",
        sa.Column("override_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("scope_type", sa.String(20), nullable=False,
                  comment="entity / cluster / circle / global"),
        sa.Column("scope_id", sa.String(100), nullable=False),
        sa.Column("action", sa.String(20), nullable=False,
                  comment="block / boost / pin"),
        sa.Column("weight_delta", sa.Numeric(5, 2), nullable=True,
                  comment="boost 时的分数增量"),
        sa.Column("pin_position", sa.Integer, nullable=True,
                  comment="pin 时插入的位置索引"),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_oo_scope", "operator_overrides", ["scope_type", "scope_id"])
    op.create_index("ix_oo_active", "operator_overrides", ["is_active"])

    # ── 14. live_risk_rules ───────────────────────────────────────────────────
    op.create_table(
        "live_risk_rules",
        sa.Column("rule_id", sa.String(80), primary_key=True),
        sa.Column("rule_type", sa.String(50), nullable=False,
                  comment="venue_closure / crowd_alert / weather_risk / custom"),
        sa.Column("name_zh", sa.String(200), nullable=False),
        sa.Column("description_zh", sa.Text, nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warning",
                  comment="info / warning / critical"),
        sa.Column("condition_json", postgresql.JSONB, nullable=False,
                  comment="规则条件，与 Python LiveRiskRule 协议对应"),
        sa.Column("action_template_zh", sa.Text, nullable=True,
                  comment="建议用户操作的文案模板"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_lrr_rule_type", "live_risk_rules", ["rule_type"])
    op.create_index("ix_lrr_active", "live_risk_rules", ["is_active"])


def downgrade() -> None:
    # 按照依赖逆序删除
    op.drop_table("live_risk_rules")
    op.drop_table("operator_overrides")
    op.drop_table("generation_decisions")
    op.drop_table("page_hero_registry")
    op.drop_table("corridor_alias_map")
    op.drop_table("corridors")
    op.drop_table("hotel_strategy_presets")
    op.drop_table("circle_entity_roles")
    op.drop_table("activity_clusters")
    op.drop_table("city_circles")
    op.drop_table("entity_temporal_profiles")
    op.drop_table("entity_mapping_reviews")
    op.drop_table("entity_field_provenance")
    op.drop_table("entity_alias")
