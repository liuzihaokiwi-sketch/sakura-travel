"""activity_clusters: 新增分钟级时长字段（4层时间模型）

Revision ID: 20260323_030000
Revises: 20260323_020000
Create Date: 2026-03-23

新增字段（均可为空，不破坏现有数据）：
  activity_clusters:
    - core_visit_minutes      SMALLINT  — 核心游玩分钟
    - queue_buffer_minutes    SMALLINT  — 排队缓冲
    - photo_buffer_minutes    SMALLINT  — 摄影缓冲
    - meal_buffer_minutes     SMALLINT  — 绑定餐饮耗时
    - fatigue_weight          NUMERIC(3,1) — 体力负担系数
    - queue_risk_level        VARCHAR(10)  — 排队风险等级
    - photo_intensity         VARCHAR(10)  — 摄影价值
    - best_time_window        VARCHAR(50)  — 最佳游览时间段
"""
from alembic import op
import sqlalchemy as sa

revision = "20260323_030000"
down_revision = "20260323_020000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activity_clusters",
        sa.Column("core_visit_minutes", sa.SmallInteger(), nullable=True,
                  comment="核心游玩时长（分钟），不含排队/拍照缓冲"),
    )
    op.add_column(
        "activity_clusters",
        sa.Column("queue_buffer_minutes", sa.SmallInteger(), nullable=True,
                  server_default="0",
                  comment="排队缓冲分钟数，热门景点旺季可达 60+"),
    )
    op.add_column(
        "activity_clusters",
        sa.Column("photo_buffer_minutes", sa.SmallInteger(), nullable=True,
                  server_default="0",
                  comment="重摄影用户额外耗时（分钟）"),
    )
    op.add_column(
        "activity_clusters",
        sa.Column("meal_buffer_minutes", sa.SmallInteger(), nullable=True,
                  server_default="0",
                  comment="簇绑定餐饮耗时，不含独立餐厅选择"),
    )
    op.add_column(
        "activity_clusters",
        sa.Column("fatigue_weight", sa.Numeric(3, 1), nullable=True,
                  server_default="1.0",
                  comment="体力消耗系数：0.5轻松/1.0正常/1.5耗体力"),
    )
    op.add_column(
        "activity_clusters",
        sa.Column("queue_risk_level", sa.String(10), nullable=True,
                  server_default="'low'",
                  comment="none / low / medium / high — 旺季排队风险"),
    )
    op.add_column(
        "activity_clusters",
        sa.Column("photo_intensity", sa.String(10), nullable=True,
                  server_default="'medium'",
                  comment="low / medium / high / extreme — 摄影价值"),
    )
    op.add_column(
        "activity_clusters",
        sa.Column("best_time_window", sa.String(50), nullable=True,
                  comment="如 '07:00-09:00' / 'evening' / 'anytime'"),
    )


def downgrade() -> None:
    for col in [
        "best_time_window",
        "photo_intensity",
        "queue_risk_level",
        "fatigue_weight",
        "meal_buffer_minutes",
        "photo_buffer_minutes",
        "queue_buffer_minutes",
        "core_visit_minutes",
    ]:
        op.drop_column("activity_clusters", col)
