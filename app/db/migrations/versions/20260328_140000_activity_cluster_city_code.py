"""activity_cluster: add city_code column

Revision ID: 20260328_140000
Revises: 20260328_130000
Create Date: 2026-03-28 14:00:00.000000

给 ActivityCluster 加 city_code 字段，标明活动归属城市。
规划逻辑变为：城市圈 → 城市天数分配 → 城市内选活动 → 排日程。

回填规则：从 cluster_id 前缀推断城市（kyo_ → kyoto, osa_ → osaka 等）。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260328_140000"
down_revision = "20260328_130000"
branch_labels = None
depends_on = None


# cluster_id 前缀 → city_code 映射
_PREFIX_MAP = {
    "kyo_": "kyoto",
    "osa_": "osaka",
    "nara_": "nara",
    "kobe_": "kobe",
    "arima_": "arima_onsen",
    "uji_": "uji",
    # 东京圈
    "tok_": "tokyo",
    "kam_": "kamakura",
    "hak_": "hakone",
    "nik_": "nikko",
    "yok_": "yokohama",
    # 北海道
    "sap_": "sapporo",
    "ota_": "otaru",
    "hako_": "hakodate",
    "fur_": "furano",
}


def upgrade() -> None:
    op.add_column(
        "activity_clusters",
        sa.Column(
            "city_code",
            sa.String(30),
            nullable=True,
            comment="归属城市: kyoto / osaka / nara — 规划时按城市分配天数再选活动",
        ),
    )
    op.create_index(
        "ix_activity_clusters_city_code",
        "activity_clusters",
        ["city_code"],
    )

    # 回填：从 cluster_id 前缀推断
    for prefix, city in _PREFIX_MAP.items():
        op.execute(
            sa.text(
                "UPDATE activity_clusters SET city_code = :city "
                "WHERE city_code IS NULL AND cluster_id LIKE :pattern"
            ).bindparams(city=city, pattern=f"{prefix}%")
        )


def downgrade() -> None:
    op.drop_index("ix_activity_clusters_city_code", table_name="activity_clusters")
    op.drop_column("activity_clusters", "city_code")
