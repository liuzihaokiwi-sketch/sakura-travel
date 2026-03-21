"""add guide_fragments library — 6 tables

Revision ID: 20260322_020000
Revises: 20260322_010000
Create Date: 2026-03-22 02:00:00.000000

对应 H8：片段攻略库数据模型
6 tables:
  guide_fragments             — 片段主表
  fragment_entities           — 片段引用的实体
  fragment_embeddings         — 向量嵌入
  fragment_compatibility      — 片段间兼容性
  fragment_usage_stats        — 使用统计
  fragment_distillation_queue — 蒸馏工作队列

注：fragment_embeddings 当前用 JSONB 存向量，后续可迁移到 pgvector。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260322_020000'
down_revision = '20260322_010000'
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ── 1. guide_fragments（主表）────────────────────────────────────────────
    op.create_table(
        'guide_fragments',
        sa.Column('fragment_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),

        # 分类
        sa.Column('fragment_type', sa.String(20), nullable=False,
                  comment='route/decision/experience/logistics/dining/tips'),
        sa.Column('title', sa.String(200), nullable=False,
                  comment="片段标题，如'东京经典Day2：浅草→上野→秋叶原'"),
        sa.Column('summary', sa.Text(), nullable=True, comment='摘要，≤200字，用于检索展示'),

        # metadata filter 字段
        sa.Column('city_code', sa.String(30), nullable=False,
                  comment='tokyo/kyoto/osaka/hokkaido/...'),
        sa.Column('area_code', sa.String(30), nullable=True,
                  comment='shinjuku/asakusa/gion/namba/...'),
        sa.Column('theme_families', postgresql.JSONB(), nullable=True,
                  comment='["classic_first","couple_aesthetic"]'),
        sa.Column('party_types', postgresql.JSONB(), nullable=True,
                  comment='["couple","solo","friends"]'),
        sa.Column('budget_levels', postgresql.JSONB(), nullable=True,
                  comment='["mid","premium"]'),
        sa.Column('season_tags', postgresql.JSONB(), nullable=True,
                  comment='["spring","cherry_blossom","all_year"]'),
        sa.Column('day_index_hint', sa.SmallInteger(), nullable=True,
                  comment='建议放第几天（0=到达日, null=不限）'),
        sa.Column('duration_slot', sa.String(20), nullable=True,
                  comment='morning/afternoon/evening/full_day/half_day'),

        # 正文
        sa.Column('body_skeleton', postgresql.JSONB(), nullable=False,
                  comment='骨架结构 JSON（实体列表+时间轴+交通+注意事项）'),
        sa.Column('body_prose', sa.Text(), nullable=True,
                  comment='润色后的可读文案'),
        sa.Column('body_html', sa.Text(), nullable=True,
                  comment='渲染好的 HTML 片段，可直接嵌入报告'),

        # 质量与来源
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='5.0',
                  comment='质量分 0-10，基于用户反馈+人工评审'),
        sa.Column('source_type', sa.String(20), nullable=False, server_default='manual',
                  comment='manual/ai_generated/distilled/imported'),
        sa.Column('source_trip_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='从哪个已交付行程中提炼'),
        sa.Column('author', sa.String(100), nullable=True, comment='编辑/审核人'),
        sa.Column('version', sa.SmallInteger(), nullable=False, server_default='1',
                  comment='版本号，每次修改+1'),

        # 状态
        sa.Column('status', sa.String(20), nullable=False, server_default='draft',
                  comment='draft/active/deprecated/archived'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),

        # 时间戳
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True,
                  comment='最近一次被复用的时间'),
    )
    op.create_index('ix_fragments_city_type', 'guide_fragments', ['city_code', 'fragment_type'])
    op.create_index('ix_fragments_city', 'guide_fragments', ['city_code'])
    op.create_index('ix_fragments_status', 'guide_fragments', ['status', 'is_active'])
    op.create_index('ix_fragments_quality', 'guide_fragments', ['quality_score'])

    # ── 2. fragment_entities ─────────────────────────────────────────────────
    op.create_table(
        'fragment_entities',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('fragment_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('guide_fragments.fragment_id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('entity_base.entity_id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_role', sa.String(30), nullable=False,
                  comment='primary/secondary/alternative/nearby'),
        sa.Column('slot_order', sa.SmallInteger(), nullable=True, comment='在片段内的排列顺序'),
        sa.Column('is_replaceable', sa.Boolean(), server_default='true',
                  comment='该实体是否可被同类替换'),
        sa.UniqueConstraint('fragment_id', 'entity_id', 'entity_role', name='uq_frag_entity_role'),
    )
    op.create_index('ix_fragment_entities_fragment', 'fragment_entities', ['fragment_id'])
    op.create_index('ix_fragment_entities_entity', 'fragment_entities', ['entity_id'])

    # ── 3. fragment_embeddings ───────────────────────────────────────────────
    op.create_table(
        'fragment_embeddings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('fragment_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('guide_fragments.fragment_id', ondelete='CASCADE'), nullable=False),
        sa.Column('model_name', sa.String(50), nullable=False,
                  comment='text-embedding-3-small/text-embedding-3-large/bge-m3'),
        sa.Column('embedding_dim', sa.SmallInteger(), nullable=False,
                  comment='向量维度 1536/3072/1024'),
        sa.Column('embedding_vector', postgresql.JSONB(), nullable=False,
                  comment='float[] — 嵌入向量（后续迁移 pgvector 时改为 vector 类型）'),
        sa.Column('source_text', sa.Text(), nullable=True,
                  comment='生成嵌入时使用的文本'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('fragment_id', 'model_name', name='uq_frag_embed_model'),
    )
    op.create_index('ix_fragment_embeddings_fragment', 'fragment_embeddings', ['fragment_id'])

    # ── 4. fragment_compatibility ────────────────────────────────────────────
    op.create_table(
        'fragment_compatibility',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('fragment_a_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('guide_fragments.fragment_id', ondelete='CASCADE'), nullable=False),
        sa.Column('fragment_b_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('guide_fragments.fragment_id', ondelete='CASCADE'), nullable=False),
        sa.Column('compatibility_type', sa.String(20), nullable=False,
                  comment='compatible/conflict/sequential_only/same_day_ok'),
        sa.Column('compatibility_score', sa.Float(), nullable=False, server_default='0.5',
                  comment='兼容度 0-1'),
        sa.Column('reason', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('fragment_a_id', 'fragment_b_id', name='uq_frag_compat_pair'),
    )
    op.create_index('ix_frag_compat_a', 'fragment_compatibility', ['fragment_a_id'])
    op.create_index('ix_frag_compat_b', 'fragment_compatibility', ['fragment_b_id'])

    # ── 5. fragment_usage_stats ──────────────────────────────────────────────
    op.create_table(
        'fragment_usage_stats',
        sa.Column('fragment_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('guide_fragments.fragment_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('total_hits', sa.Integer(), server_default='0', comment='总命中次数'),
        sa.Column('total_adopted', sa.Integer(), server_default='0', comment='被采纳次数'),
        sa.Column('total_rejected', sa.Integer(), server_default='0', comment='被拒绝次数'),
        sa.Column('total_replaced_by_human', sa.Integer(), server_default='0', comment='被人工替换次数'),
        sa.Column('avg_user_rating', sa.Float(), nullable=True, comment='用户平均反馈分 1-5'),
        sa.Column('positive_feedback_count', sa.Integer(), server_default='0'),
        sa.Column('negative_feedback_count', sa.Integer(), server_default='0'),
        sa.Column('conversion_contribution', sa.Float(), nullable=True,
                  comment='对成交的贡献度估计 0-1'),
        sa.Column('last_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── 6. fragment_distillation_queue ───────────────────────────────────────
    op.create_table(
        'fragment_distillation_queue',
        sa.Column('queue_id', sa.BigInteger(), autoincrement=True, primary_key=True),

        # 来源
        sa.Column('source_trip_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='来源行程 ID'),
        sa.Column('source_day_index', sa.SmallInteger(), nullable=True,
                  comment='来源行程的第几天'),
        sa.Column('source_type', sa.String(20), nullable=False,
                  comment='auto_detect/user_feedback/ops_review'),

        # 蒸馏内容
        sa.Column('proposed_type', sa.String(20), nullable=False,
                  comment='建议的片段类型'),
        sa.Column('proposed_title', sa.String(200), nullable=True),
        sa.Column('proposed_city_code', sa.String(30), nullable=True),
        sa.Column('raw_content', postgresql.JSONB(), nullable=True,
                  comment='待提炼的原始内容'),
        sa.Column('extraction_prompt', sa.Text(), nullable=True,
                  comment='用于提炼的 prompt'),

        # 处理状态
        sa.Column('status', sa.String(20), nullable=False, server_default='pending',
                  comment='pending/processing/done/rejected'),
        sa.Column('result_fragment_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='蒸馏成功后创建的 fragment_id'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('priority', sa.SmallInteger(), server_default='5',
                  comment='优先级 1-10，越大越优先'),

        # 时间戳
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_distillation_queue_status', 'fragment_distillation_queue', ['status', 'priority'])
    op.create_index('ix_distillation_queue_source', 'fragment_distillation_queue', ['source_trip_id'])


def downgrade() -> None:
    op.drop_index('ix_distillation_queue_source', table_name='fragment_distillation_queue')
    op.drop_index('ix_distillation_queue_status', table_name='fragment_distillation_queue')
    op.drop_table('fragment_distillation_queue')

    op.drop_table('fragment_usage_stats')

    op.drop_index('ix_frag_compat_b', table_name='fragment_compatibility')
    op.drop_index('ix_frag_compat_a', table_name='fragment_compatibility')
    op.drop_table('fragment_compatibility')

    op.drop_index('ix_fragment_embeddings_fragment', table_name='fragment_embeddings')
    op.drop_table('fragment_embeddings')

    op.drop_index('ix_fragment_entities_entity', table_name='fragment_entities')
    op.drop_index('ix_fragment_entities_fragment', table_name='fragment_entities')
    op.drop_table('fragment_entities')

    op.drop_index('ix_fragments_quality', table_name='guide_fragments')
    op.drop_index('ix_fragments_status', table_name='guide_fragments')
    op.drop_index('ix_fragments_city', table_name='guide_fragments')
    op.drop_index('ix_fragments_city_type', table_name='guide_fragments')
    op.drop_table('guide_fragments')
