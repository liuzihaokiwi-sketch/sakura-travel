#!/usr/bin/env python3
"""
创建软规则系统数据库迁移脚本
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# 迁移信息
revision = 'soft_rules_system_v1'
down_revision = 'a1b2c3d4e5f6'  # 初始 schema 的 revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── entity_soft_scores ──
    op.create_table('entity_soft_scores',
        sa.Column('entity_type', sa.String(20), primary_key=True, comment='poi / hotel / restaurant'),
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('emotional_value', sa.Numeric(3, 1), comment='情绪价值/氛围感 0-10'),
        sa.Column('shareability', sa.Numeric(3, 1), comment='分享感/出片回报 0-10'),
        sa.Column('relaxation_feel', sa.Numeric(3, 1), comment='松弛感/不赶感 0-10'),
        sa.Column('memory_point', sa.Numeric(3, 1), comment='记忆点强度 0-10'),
        sa.Column('localness', sa.Numeric(3, 1), comment='当地感/不模板感 0-10'),
        sa.Column('smoothness', sa.Numeric(3, 1), comment='顺滑感/少折腾感 0-10'),
        sa.Column('food_certainty', sa.Numeric(3, 1), comment='餐饮确定感 0-10'),
        sa.Column('night_completion', sa.Numeric(3, 1), comment='夜间完成度 0-10'),
        sa.Column('recovery_friendliness', sa.Numeric(3, 1), comment='恢复友好度 0-10'),
        sa.Column('weather_resilience_soft', sa.Numeric(3, 1), comment='雨天韧性 0-10'),
        sa.Column('professional_judgement_feel', sa.Numeric(3, 1), comment='专业判断感 0-10'),
        sa.Column('preview_conversion_power', sa.Numeric(3, 1), comment='免费Day1杀伤力 0-10'),
        sa.Column('score_sources', JSONB(), comment='每个维度的来源 ai/stat/manual'),
        sa.Column('score_version', sa.String(50), comment='评分引擎版本号'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
        sa.Index('ix_entity_soft_scores_type_calculated', 'entity_type', 'calculated_at'),
    )
    
    # ── editorial_seed_overrides ──
    op.create_table('editorial_seed_overrides',
        sa.Column('entity_type', sa.String(20), primary_key=True, comment='poi / hotel / restaurant'),
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('dimension_id', sa.String(50), primary_key=True, comment='维度标识，如 emotional_value'),
        sa.Column('override_value', sa.Numeric(3, 1), nullable=False, comment='0-10'),
        sa.Column('reason', sa.Text(), comment='修正理由'),
        sa.Column('editor_id', sa.String(100), comment='编辑ID'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
    )
    
    # ── soft_rule_explanations ──
    op.create_table('soft_rule_explanations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(20), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('dimension_id', sa.String(50), nullable=False),
        sa.Column('score', sa.Numeric(3, 1), nullable=False, comment='0-10'),
        sa.Column('explanation', sa.Text(), comment='一句话理由'),
        sa.Column('source', sa.String(20), nullable=False, comment='ai / stat / manual'),
        sa.Column('score_version', sa.String(50), comment='评分引擎版本号'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
        sa.Index('ix_soft_rule_explanations_entity_dimension', 'entity_type', 'entity_id', 'dimension_id'),
    )
    
    # ── segment_weight_packs ──
    op.create_table('segment_weight_packs',
        sa.Column('pack_id', sa.String(50), primary_key=True, comment='客群标识，如 couple'),
        sa.Column('name_cn', sa.String(100), nullable=False, comment='中文名'),
        sa.Column('description', sa.Text(), comment='核心目标描述'),
        sa.Column('weights', JSONB(), nullable=False, comment='12维度权重'),
        sa.Column('top_dimensions', JSONB(), comment='最在意的维度列表'),
        sa.Column('low_dimensions', JSONB(), comment='不太在意的维度列表'),
        sa.Column('day1_trigger', sa.Text(), comment='Day1敏感触发点'),
        sa.Column('repurchase_trigger', sa.Text(), comment='复购触发点'),
        sa.Column('tuning_sensitivity', JSONB(), comment='微调敏感模块'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # ── stage_weight_packs ──
    op.create_table('stage_weight_packs',
        sa.Column('pack_id', sa.String(50), primary_key=True, comment='阶段标识，如 preview_day1'),
        sa.Column('name_cn', sa.String(100), nullable=False, comment='中文名'),
        sa.Column('description', sa.Text(), comment='核心目标描述'),
        sa.Column('weights', JSONB(), nullable=False, comment='12维度权重'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # ── preview_trigger_scores ──
    op.create_table('preview_trigger_scores',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('itinerary_day_id', UUID(as_uuid=True), nullable=False),
        sa.Column('visual_appeal', sa.Numeric(5, 2), nullable=False, comment='视觉吸引力 0-100'),
        sa.Column('wow_factor', sa.Numeric(5, 2), nullable=False, comment='惊喜因子 0-100'),
        sa.Column('variety', sa.Numeric(5, 2), nullable=False, comment='多样性 0-100'),
        sa.Column('evidence_density', sa.Numeric(5, 2), nullable=False, comment='证据密度 0-100'),
        sa.Column('route_compactness', sa.Numeric(5, 2), nullable=False, comment='路线紧凑度 0-100'),
        sa.Column('preview_score', sa.Numeric(5, 2), nullable=False, comment='预览总分 0-100'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['itinerary_day_id'], ['itinerary_days.itinerary_day_id'], ondelete='CASCADE'),
        sa.Index('ix_preview_trigger_scores_day_id', 'itinerary_day_id'),
    )
    
    # ── swap_candidate_soft_scores ──
    op.create_table('swap_candidate_soft_scores',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('original_entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('slot_type', sa.String(50), nullable=False, comment='时段类型，如 morning_lunch'),
        sa.Column('compatibility_score', sa.Numeric(5, 2), nullable=False, comment='兼容性分 0-100'),
        sa.Column('differentiation_score', sa.Numeric(5, 2), nullable=False, comment='差异化分 0-100'),
        sa.Column('soft_rule_score', sa.Numeric(5, 2), nullable=False, comment='软规则分 0-100'),
        sa.Column('total_score', sa.Numeric(5, 2), nullable=False, comment='总分 0-100'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['original_entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['candidate_entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
        sa.Index('ix_swap_candidate_soft_scores_original', 'original_entity_id', 'slot_type'),
        sa.Index('ix_swap_candidate_soft_scores_candidate', 'candidate_entity_id'),
    )
    
    # ── soft_rule_feedback_log ──
    op.create_table('soft_rule_feedback_log',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False, comment='反馈类型，如 preview_view / swap_triggered'),
        sa.Column('feedback_value', sa.Numeric(5, 2), comment='反馈值，如停留秒数/满意度分'),
        sa.Column('metadata', JSONB(), comment='元数据'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
        sa.Index('ix_soft_rule_feedback_log_entity_type', 'entity_id', 'feedback_type'),
    )
    
    # ── area_profiles ──
    op.create_table('area_profiles',
        sa.Column('area_code', sa.String(50), primary_key=True),
        sa.Column('city_code', sa.String(50), nullable=False),
        sa.Column('area_type', sa.String(20), nullable=False, comment='商业/住宅/观光/美食'),
        sa.Column('best_time_slots', JSONB(), comment='最佳时段列表'),
        sa.Column('peak_months', JSONB(), comment='旺季月份'),
        sa.Column('crowd_pattern_json', JSONB(), comment='人流模式'),
        sa.Column('nearest_station', sa.String(100), comment='最近车站'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Index('ix_area_profiles_city_code', 'city_code'),
    )
    
    # ── timeslot_rules ──
    op.create_table('timeslot_rules',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('valid_slots', JSONB(), nullable=False, comment='有效时段 morning/afternoon/evening/night'),
        sa.Column('best_slot', sa.String(20), nullable=False, comment='最佳时段'),
        sa.Column('closed_slots', JSONB(), comment='关闭时段列表'),
        sa.Column('reason', sa.Text(), comment='原因说明'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
        sa.Index('ix_timeslot_rules_entity_id', 'entity_id'),
    )
    
    # ── seasonal_events ──
    op.create_table('seasonal_events',
        sa.Column('event_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('city_code', sa.String(50), nullable=False),
        sa.Column('area_code', sa.String(50)),
        sa.Column('event_name', sa.String(200), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('crowd_impact', sa.String(20), nullable=False, comment='high/medium/low'),
        sa.Column('booking_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('best_timing_tips', sa.Text(), comment='最佳时机提示'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Index('ix_seasonal_events_city_date', 'city_code', 'start_date', 'end_date'),
    )
    
    # ── transport_links ──
    op.create_table('transport_links',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('origin_area', sa.String(50), nullable=False),
        sa.Column('dest_area', sa.String(50), nullable=False),
        sa.Column('mode', sa.String(20), nullable=False, comment='交通方式 train/bus/taxi/walk'),
        sa.Column('typical_duration_min', sa.Integer(), nullable=False, comment='典型时长（分钟）'),
        sa.Column('cost_jpy', sa.Integer(), comment='费用（日元）'),
        sa.Column('rush_hour_penalty_min', sa.Integer(), comment='高峰时段额外时长（分钟）'),
        sa.Column('last_train_time', sa.String(10), comment='末班车时间 HH:MM'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Index('ix_transport_links_origin_dest', 'origin_area', 'dest_area'),
    )
    
    # ── audience_fit ──
    op.create_table('audience_fit',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('audience_type', sa.String(20), nullable=False, comment='couple/family/solo/senior/group'),
        sa.Column('fit_score', sa.SmallInteger(), nullable=False, comment='适配分 1-5'),
        sa.Column('reason', sa.Text(), comment='适配理由'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
        sa.Index('ix_audience_fit_entity_audience', 'entity_id', 'audience_type'),
    )
    
    # ── entity_operating_facts ──
    op.create_table('entity_operating_facts',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('day_of_week', sa.String(10), nullable=False, comment='星期几 mon/tue/wed/thu/fri/sat/sun'),
        sa.Column('open_time', sa.String(10), comment='开门时间 HH:MM'),
        sa.Column('close_time', sa.String(10), comment='关门时间 HH:MM'),
        sa.Column('last_entry_time', sa.String(10), comment='最后入场时间 HH:MM'),
        sa.Column('holiday_schedule', JSONB(), comment='节假日安排'),
        sa.Column('reservation_window_days', sa.Integer(), comment='预订提前天数'),
        sa.Column('typical_wait_min', sa.Integer(), comment='典型等待时间（分钟）'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entity_id'], ['entity_base.entity_id'], ondelete='CASCADE'),
        sa.Index('ix_entity_operating_facts_entity_day', 'entity_id', 'day_of_week'),
    )
    
    # ── product_config ──
    op.create_table('product_config',
        sa.Column('config_key', sa.String(100), primary_key=True),
        sa.Column('config_value', JSONB(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # ── feature_flags ──
    op.create_table('feature_flags',
        sa.Column('flag_key', sa.String(100), primary_key=True),
        sa.Column('flag_value', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.Text(), comment='功能描述'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # ── user_events ──
    op.create_table('user_events',
        sa.Column('event_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True)),
        sa.Column('session_id', sa.String(100), comment='会话ID'),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', JSONB(), comment='事件数据'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.Index('ix_user_events_user_type', 'user_id', 'event_type'),
        sa.Index('ix_user_events_created_at', 'created_at'),
    )
    
    # ── 修改现有表 ──
    
    # 修改 entity_scores 表，增加 preview_score 和 context_score
    op.add_column('entity_scores',
        sa.Column('preview_score', sa.Numeric(5, 2), comment='预览分 0-100')
    )
    op.add_column('entity_scores',
        sa.Column('context_score', sa.Numeric(5, 2), comment='上下文分 0-100')
    )
    
    # 修改 entity_scores 表，增加 soft_rule_score 等4个字段
    op.add_column('entity_scores',
        sa.Column('soft_rule_score', sa.Numeric(5, 2), comment='软规则分 0-100')
    )
    op.add_column('entity_scores',
        sa.Column('soft_rule_breakdown', JSONB(), comment='软规则维度分详情')
    )
    op.add_column('entity_scores',
        sa.Column('segment_pack_id', sa.String(50), comment='使用的客群权重包')
    )
    op.add_column('entity_scores',
        sa.Column('stage_pack_id', sa.String(50), comment='使用的阶段权重包')
    )
    
    # 修改 itinerary_items 表，增加 swap_candidates JSONB
    op.add_column('itinerary_items',
        sa.Column('swap_candidates', JSONB(), comment='替换候选列表')
    )


def downgrade() -> None:
    # 删除新增的表
    op.drop_table('user_events')
    op.drop_table('feature_flags')
    op.drop_table('product_config')
    op.drop_table('entity_operating_facts')
    op.drop_table('audience_fit')
    op.drop_table('transport_links')
    op.drop_table('seasonal_events')
    op.drop_table('timeslot_rules')
    op.drop_table('area_profiles')
    op.drop_table('soft_rule_feedback_log')
    op.drop_table('swap_candidate_soft_scores')
    op.drop_table('preview_trigger_scores')
    op.drop_table('stage_weight_packs')
    op.drop_table('segment_weight_packs')
    op.drop_table('soft_rule_explanations')
    op.drop_table('editorial_seed_overrides')
    op.drop_table('entity_soft_scores')
    
    # 删除新增的列
    op.drop_column('itinerary_items', 'swap_candidates')
    op.drop_column('entity_scores', 'stage_pack_id')
    op.drop_column('entity_scores', 'segment_pack_id')
    op.drop_column('entity_scores', 'soft_rule_breakdown')
    op.drop_column('entity_scores', 'soft_rule_score')
    op.drop_column('entity_scores', 'context_score')
    op.drop_column('entity_scores', 'preview_score')


if __name__ == "__main__":
    # 生成迁移文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    migration_filename = f"{timestamp}_soft_rules_system_v1.py"
    migration_path = project_root / "app" / "db" / "migrations" / "versions" / migration_filename
    
    # 创建迁移文件内容
    migration_content = f'''"""soft_rules_system_v1 — 创建软规则系统相关表

Revision ID: {revision}
Revises: {down_revision}
Create Date: {datetime.now().isoformat()}

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision: str = "{revision}"
down_revision: Union[str, None] = "{down_revision}"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    {indent(upgrade.__code__, 4)}


def downgrade() -> None:
    {indent(downgrade.__code__, 4)}
'''
    
    # 保存迁移文件
    migration_path.write_text(migration_content)
    print(f"迁移文件已创建: {migration_path}")


def indent(code_obj, spaces):
    """缩进代码"""
    import inspect
    source = inspect.getsource(code_obj)
    lines = source.split('\n')
    indented = '\n'.join(' ' * spaces + line for line in lines)
    return indented