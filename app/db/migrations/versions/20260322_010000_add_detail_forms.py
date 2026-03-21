"""add detail_forms and detail_form_steps tables

Revision ID: 20260322_010000
Revises: 20260321_210000
Create Date: 2026-03-22 01:00:00.000000

对应 H5：付费后详细表单 6 步数据模型
2 tables: detail_forms, detail_form_steps
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260322_010000'
down_revision = '20260321_210000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── detail_forms ──────────────────────────────────────────────────────────
    op.create_table(
        'detail_forms',
        sa.Column('form_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('submission_id', sa.String(50), nullable=False, unique=True, comment='quiz_submissions.id — 一对一关联'),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.order_id', ondelete='SET NULL'), nullable=True, comment='付费订单 ID'),

        # 表单进度
        sa.Column('current_step', sa.SmallInteger(), nullable=False, server_default='1', comment='当前填到第几步 (1-6)'),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false', comment='是否全部 6 步填写完成'),

        # Step 1: 目的地与日期
        sa.Column('cities', postgresql.JSONB(), nullable=True, comment='[{"city_code":"tokyo","city_name":"东京","nights":3,"place_id":"xxx"}]'),
        sa.Column('travel_start_date', sa.String(10), nullable=True, comment='YYYY-MM-DD'),
        sa.Column('travel_end_date', sa.String(10), nullable=True, comment='YYYY-MM-DD'),
        sa.Column('duration_days', sa.SmallInteger(), nullable=True),
        sa.Column('date_flexible', sa.Boolean(), server_default='false', comment='日期是否灵活'),

        # Step 2: 同行人信息
        sa.Column('party_type', sa.String(30), nullable=True, comment='solo/couple/family_with_kids/family_no_kids/friends/senior'),
        sa.Column('party_size', sa.SmallInteger(), nullable=True),
        sa.Column('party_ages', postgresql.JSONB(), nullable=True, comment='[28, 30]'),
        sa.Column('has_elderly', sa.Boolean(), server_default='false'),
        sa.Column('has_children', sa.Boolean(), server_default='false'),
        sa.Column('children_ages', postgresql.JSONB(), nullable=True, comment='[5, 3]'),
        sa.Column('special_needs', sa.Text(), nullable=True, comment='轮椅/素食等特殊需求'),

        # Step 3: 预算与住宿
        sa.Column('budget_level', sa.String(20), nullable=True, comment='budget/mid/premium/luxury'),
        sa.Column('budget_total_jpy', sa.Integer(), nullable=True, comment='总预算（日元，不含机票）'),
        sa.Column('accommodation_pref', postgresql.JSONB(), nullable=True, comment='["hotel","ryokan","hostel"]'),
        sa.Column('hotel_area_pref', sa.Text(), nullable=True, comment='偏好住在哪个区域'),
        sa.Column('hotel_booking_status', sa.String(20), nullable=True, comment='none/partial/all'),
        sa.Column('booked_hotels', postgresql.JSONB(), nullable=True, comment='[{"city":"tokyo","name":"xx","checkin":"2026-04-01"}]'),

        # Step 4: 兴趣偏好
        sa.Column('must_have_tags', postgresql.JSONB(), nullable=True, comment='["onsen","teamlab","nishiki_market"]'),
        sa.Column('nice_to_have_tags', postgresql.JSONB(), nullable=True),
        sa.Column('avoid_tags', postgresql.JSONB(), nullable=True, comment='不想去/不喜欢的类型'),
        sa.Column('food_preferences', postgresql.JSONB(), nullable=True, comment='["ramen","sushi","vegetarian"]'),
        sa.Column('food_restrictions', postgresql.JSONB(), nullable=True, comment='["no_pork","halal"]'),
        sa.Column('food_restrictions_note', sa.Text(), nullable=True),
        sa.Column('must_go_places', postgresql.JSONB(), nullable=True, comment='用户指定必去地点'),
        sa.Column('dont_want_places', postgresql.JSONB(), nullable=True, comment='用户指定不想去地点'),

        # Step 5: 行程节奏
        sa.Column('pace_preference', sa.String(20), nullable=True, comment='relaxed/moderate/intensive'),
        sa.Column('trip_style', sa.String(20), nullable=True, comment='one_city/multi_city/scenic_loop'),
        sa.Column('stamina_level', sa.String(10), nullable=True, comment='low/mid/high'),
        sa.Column('wake_up_time', sa.String(5), nullable=True, comment='HH:MM'),
        sa.Column('fixed_events', postgresql.JSONB(), nullable=True, comment='[{"date":"2026-04-02","time":"14:00","place":"teamlab"}]'),
        sa.Column('free_text_wishes', sa.Text(), nullable=True, comment='用户自由填写的愿望'),

        # Step 6: 航班与交通
        sa.Column('transport_locked', sa.Boolean(), server_default='false', comment='是否已购交通票'),
        sa.Column('arrival_date', sa.String(10), nullable=True, comment='YYYY-MM-DD'),
        sa.Column('arrival_time', sa.String(5), nullable=True, comment='HH:MM'),
        sa.Column('arrival_place', sa.String(100), nullable=True, comment='到达机场/车站'),
        sa.Column('departure_date', sa.String(10), nullable=True, comment='YYYY-MM-DD'),
        sa.Column('departure_time', sa.String(5), nullable=True, comment='HH:MM'),
        sa.Column('departure_place', sa.String(100), nullable=True, comment='离开机场/车站'),
        sa.Column('has_jr_pass', sa.Boolean(), server_default='false'),
        sa.Column('jr_pass_type', sa.String(50), nullable=True, comment='7day/14day/21day/regional'),
        sa.Column('has_pocket_wifi', sa.Boolean(), server_default='false'),
        sa.Column('transport_notes', sa.Text(), nullable=True),

        # 校验结果缓存
        sa.Column('validation_result', postgresql.JSONB(), nullable=True, comment='最近一次校验结果（红黄绿）'),
        sa.Column('validation_status', sa.String(20), nullable=True, comment='red/yellow/green'),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),

        # 时间戳
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True, comment='用户点击提交的时间'),
    )
    op.create_index('ix_detail_forms_submission', 'detail_forms', ['submission_id'])
    op.create_index('ix_detail_forms_order', 'detail_forms', ['order_id'])
    op.create_index('ix_detail_forms_complete', 'detail_forms', ['is_complete'])
    op.create_index('ix_detail_forms_validation', 'detail_forms', ['validation_status'])

    # ── detail_form_steps ─────────────────────────────────────────────────────
    op.create_table(
        'detail_form_steps',
        sa.Column('step_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('form_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('detail_forms.form_id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.SmallInteger(), nullable=False, comment='1-6'),
        sa.Column('step_data', postgresql.JSONB(), nullable=True, comment='该步骤的完整数据快照'),
        sa.Column('is_complete', sa.Boolean(), server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('form_id', 'step_number', name='uq_detail_form_steps_form_step'),
    )
    op.create_index('ix_detail_form_steps_form', 'detail_form_steps', ['form_id'])


def downgrade() -> None:
    op.drop_index('ix_detail_form_steps_form', table_name='detail_form_steps')
    op.drop_table('detail_form_steps')

    op.drop_index('ix_detail_forms_validation', table_name='detail_forms')
    op.drop_index('ix_detail_forms_complete', table_name='detail_forms')
    op.drop_index('ix_detail_forms_order', table_name='detail_forms')
    op.drop_index('ix_detail_forms_submission', table_name='detail_forms')
    op.drop_table('detail_forms')
