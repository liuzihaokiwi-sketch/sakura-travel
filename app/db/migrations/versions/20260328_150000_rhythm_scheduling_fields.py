"""activity_cluster: add rhythm scheduling fields

Revision ID: 20260328_150000
Revises: 20260328_140000
Create Date: 2026-03-28 15:00:00.000000

新增节奏编排三字段：
  experience_family — 体验家族（同族不连续两天）
  rhythm_role       — 节奏角色（peak 间隔 recovery）
  energy_level      — 精力消耗（high 后跟 low/medium）

排程硬规则：
  1. 相邻两天 experience_family 不能相同
  2. 两个 peak 之间至少隔一个 recovery 或 contrast
  3. energy_level=high 后面必须跟 medium 或 low

回填规则：从现有 primary_corridor / fatigue_weight / trip_role 推断。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260328_150000"
down_revision = "20260328_140000"
branch_labels = None
depends_on = None


# 现有 primary_corridor → experience_family 的推断映射
_CORRIDOR_TO_FAMILY = {
    "higashiyama": "shrine", "arashiyama": "shrine", "fushimi": "shrine",
    "kinugasa": "shrine", "okazaki": "shrine", "kyo_zen_garden": "shrine",
    "namba": "food", "hakata": "food", "tsukiji": "food",
    "sakurajima": "themepark", "maihama": "themepark",
    "hakone": "onsen", "arima": "onsen", "noboribetsu": "onsen",
    "furano": "flower", "biei": "flower",
    "shinjuku": "citynight", "shibuya": "citynight",
}

# 现有 trip_role → rhythm_role 的推断映射
_ROLE_TO_RHYTHM = {
    "anchor": "peak",
    "enrichment": "contrast",
    "buffer": "utility",
}


def upgrade() -> None:
    op.add_column("activity_clusters", sa.Column(
        "experience_family", sa.String(20), nullable=True,
        comment="体验家族: flower/mountain/sea/shrine/citynight/art/food/locallife/themepark/onsen",
    ))
    op.add_column("activity_clusters", sa.Column(
        "rhythm_role", sa.String(20), nullable=True,
        comment="节奏角色: peak/contrast/recovery/utility",
    ))
    op.add_column("activity_clusters", sa.Column(
        "energy_level", sa.String(10), nullable=True,
        comment="精力消耗: low/medium/high",
    ))

    op.create_index("ix_activity_clusters_experience_family", "activity_clusters", ["experience_family"])
    op.create_index("ix_activity_clusters_rhythm_role", "activity_clusters", ["rhythm_role"])

    # 回填 rhythm_role 从 trip_role
    for old_role, new_role in _ROLE_TO_RHYTHM.items():
        op.execute(sa.text(
            "UPDATE activity_clusters SET rhythm_role = :new "
            "WHERE rhythm_role IS NULL AND trip_role = :old"
        ).bindparams(new=new_role, old=old_role))

    # 回填 energy_level 从 fatigue_weight
    op.execute(sa.text(
        "UPDATE activity_clusters SET energy_level = 'low' "
        "WHERE energy_level IS NULL AND fatigue_weight IS NOT NULL AND fatigue_weight < 0.8"
    ))
    op.execute(sa.text(
        "UPDATE activity_clusters SET energy_level = 'medium' "
        "WHERE energy_level IS NULL AND fatigue_weight IS NOT NULL AND fatigue_weight >= 0.8 AND fatigue_weight <= 1.2"
    ))
    op.execute(sa.text(
        "UPDATE activity_clusters SET energy_level = 'high' "
        "WHERE energy_level IS NULL AND fatigue_weight IS NOT NULL AND fatigue_weight > 1.2"
    ))

    # 回填 experience_family 从 primary_corridor（部分匹配）
    for corridor, family in _CORRIDOR_TO_FAMILY.items():
        op.execute(sa.text(
            "UPDATE activity_clusters SET experience_family = :family "
            "WHERE experience_family IS NULL AND primary_corridor LIKE :pattern"
        ).bindparams(family=family, pattern=f"%{corridor}%"))


def downgrade() -> None:
    op.drop_index("ix_activity_clusters_rhythm_role", table_name="activity_clusters")
    op.drop_index("ix_activity_clusters_experience_family", table_name="activity_clusters")
    op.drop_column("activity_clusters", "energy_level")
    op.drop_column("activity_clusters", "rhythm_role")
    op.drop_column("activity_clusters", "experience_family")
