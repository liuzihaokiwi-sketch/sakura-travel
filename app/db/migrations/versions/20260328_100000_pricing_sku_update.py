"""upsert product SKU pricing: ¥198 base + ¥20/day + ¥29 split-volume

Revision ID: 20260328_100000
Revises: 20260327_120000
Create Date: 2026-03-28 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260328_100000"
down_revision = "20260327_120000"
branch_labels = None
depends_on = None


# SKU 定义
# 定价规则：
#   标准版  ¥198 基础（含5天），每多1天 +¥20，国际圈 +¥50
#   拆册版  ¥29/册（单城单日，DIY 拼装）
#   速览版  ¥98（固定3天模板，无个性化）

_SKUS = [
    # (sku_id, sku_name, price_cny, sku_type, max_days, features_json)
    (
        "standard_198",
        "关西经典·个性化手账本",
        198.00,
        "personalized",
        10,
        {
            "workflow_config": {
                "mode": "auto_generate",
                "base_days": 5,
                "extra_day_price": 20,
                "max_days": 10,
            },
            "sections": [
                "daily_timeline",
                "route_map",
                "spot_info",
                "area_hotel_tip",
                "transport_pass_guide",
                "restaurant_report",
                "pre_trip_guide",
                "avoid_traps",
            ],
            "has_restaurant": True,
            "has_hotel_filter": True,
            "custom_input": True,
            "diy_zone": True,
        },
    ),
    (
        "single_册_29",
        "单城单日·拆册版",
        29.00,
        "template",
        1,
        {
            "workflow_config": {
                "mode": "template",
                "fixed_days": 1,
            },
            "sections": [
                "daily_timeline",
                "spot_info",
                "restaurant_report",
            ],
            "has_restaurant": True,
            "has_hotel_filter": False,
            "custom_input": False,
            "diy_zone": True,
            "is_split_volume": True,
        },
    ),
    (
        "quick_98",
        "速览版·3天模板行程",
        98.00,
        "template",
        3,
        {
            "workflow_config": {
                "mode": "template",
                "fixed_days": 3,
            },
            "sections": [
                "daily_timeline",
                "route_map",
                "spot_info",
                "area_hotel_tip",
                "basic_transport",
                "pre_trip_guide",
            ],
            "has_restaurant": False,
            "has_hotel_filter": False,
            "custom_input": False,
            "diy_zone": False,
        },
    ),
]


def upgrade() -> None:
    conn = op.get_bind()

    for sku_id, sku_name, price_cny, sku_type, max_days, features in _SKUS:
        import json
        conn.execute(
            sa.text("""
                INSERT INTO product_sku
                    (sku_id, sku_name, price_cny, sku_type, max_days, features, is_active)
                VALUES
                    (:sku_id, :sku_name, :price_cny, :sku_type, :max_days, :features::jsonb, true)
                ON CONFLICT (sku_id) DO UPDATE SET
                    sku_name    = EXCLUDED.sku_name,
                    price_cny   = EXCLUDED.price_cny,
                    sku_type    = EXCLUDED.sku_type,
                    max_days    = EXCLUDED.max_days,
                    features    = EXCLUDED.features,
                    is_active   = true
            """),
            {
                "sku_id": sku_id,
                "sku_name": sku_name,
                "price_cny": price_cny,
                "sku_type": sku_type,
                "max_days": max_days,
                "features": json.dumps(features, ensure_ascii=False),
            },
        )

    # 下线旧的 basic_20 / basic_v1 等遗留 SKU
    conn.execute(
        sa.text("""
            UPDATE product_sku SET is_active = false
            WHERE sku_id IN ('basic_20', 'basic_v1', 'flex_68', 'premium_298')
        """)
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM product_sku WHERE sku_id IN ('standard_198','single_册_29','quick_98')")
    )
    conn.execute(
        sa.text("""
            UPDATE product_sku SET is_active = true
            WHERE sku_id IN ('basic_20', 'basic_v1', 'flex_68', 'premium_298')
        """)
    )
