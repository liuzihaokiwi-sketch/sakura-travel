"""add eval_runs, eval_results, eval_failure_attributions tables

Revision ID: 20260322_030000
Revises: 20260322_020000
Create Date: 2026-03-22 03:00:00.000000

对应 E14：评测飞轮持久化存储
3 tables:
  eval_runs                  — 每次评测运行汇总
  eval_results               — 单 case 运行结果
  eval_failure_attributions  — 失败归因
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260322_030000'
down_revision = '20260322_020000'
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ── eval_runs ────────────────────────────────────────────────────────────
    op.create_table(
        'eval_runs',
        sa.Column('run_id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('run_name', sa.String(200), nullable=False,
                  comment='如 regression-20260322_010000'),
        sa.Column('suite', sa.String(50), nullable=True,
                  comment='standard/regression/high_value/all'),
        sa.Column('case_ids', postgresql.JSONB(), nullable=True,
                  comment='本次运行的 case ID 列表'),
        sa.Column('generation_config', postgresql.JSONB(), nullable=True,
                  comment='覆盖生成管线参数'),
        sa.Column('compare_with_run_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='对比基线 run ID'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending',
                  comment='pending/running/done/error'),
        sa.Column('total_cases', sa.Integer(), server_default='0'),
        sa.Column('passed', sa.Integer(), server_default='0'),
        sa.Column('failed', sa.Integer(), server_default='0'),
        sa.Column('borderline', sa.Integer(), server_default='0'),
        sa.Column('errored', sa.Integer(), server_default='0'),
        sa.Column('pass_rate', sa.Float(), nullable=True),
        sa.Column('avg_composite_score', sa.Float(), nullable=True),
        sa.Column('avg_structure_score', sa.Float(), nullable=True),
        sa.Column('avg_planning_score', sa.Float(), nullable=True),
        sa.Column('avg_user_value_score', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_eval_runs_status', 'eval_runs', ['status'])
    op.create_index('ix_eval_runs_suite', 'eval_runs', ['suite'])
    op.create_index('ix_eval_runs_created', 'eval_runs', ['created_at'])

    # ── eval_results ─────────────────────────────────────────────────────────
    op.create_table(
        'eval_results',
        sa.Column('result_id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('eval_runs.run_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('case_id', sa.String(50), nullable=False,
                  comment='如 C001, H001, R003'),
        sa.Column('case_type', sa.String(30), nullable=True,
                  comment='standard/high_value/constrained/edge/regression'),
        sa.Column('generated_trip_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='生成的行程 ID'),
        sa.Column('generation_trace_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='对应 generation_run.run_id，E9 接入后自动填充'),
        sa.Column('generation_duration_ms', sa.Integer(), nullable=True),

        # grader 输出
        sa.Column('structure_score', sa.Float(), nullable=True,
                  comment='结构层得分 0-100'),
        sa.Column('planning_score', sa.Float(), nullable=True,
                  comment='规划层得分 0-100'),
        sa.Column('user_value_score', sa.Float(), nullable=True,
                  comment='体验层得分 0-100'),
        sa.Column('input_score', sa.Float(), nullable=True,
                  comment='输入理解层得分 0-100'),
        sa.Column('composite_score', sa.Float(), nullable=True,
                  comment='加权综合分：structure×0.3 + planning×0.4 + user_value×0.3'),
        sa.Column('grader_outputs', postgresql.JSONB(), nullable=True,
                  comment='各 grader 的完整输出 JSON'),
        sa.Column('overall_verdict', sa.String(20), nullable=False, server_default='skipped',
                  comment='pass/fail/borderline/error/skipped'),
        sa.Column('passed', sa.Boolean(), server_default='false'),
        sa.Column('issues', postgresql.JSONB(), nullable=True,
                  comment='所有 grader 收集的问题列表'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_eval_results_run', 'eval_results', ['run_id'])
    op.create_index('ix_eval_results_case', 'eval_results', ['case_id'])
    op.create_index('ix_eval_results_verdict', 'eval_results', ['overall_verdict'])
    op.create_index('ix_eval_results_run_case', 'eval_results', ['run_id', 'case_id'])

    # ── eval_failure_attributions ─────────────────────────────────────────────
    op.create_table(
        'eval_failure_attributions',
        sa.Column('attribution_id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('result_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('eval_results.result_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', sa.String(50), nullable=False),

        # 归因结果
        sa.Column('primary_layer', sa.String(50), nullable=False,
                  comment='input_understanding/fragment_hit/hard_rule/soft_rule/template_assembly/ai_explanation/render_delivery'),
        sa.Column('secondary_layers', postgresql.JSONB(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False,
                  comment='归因置信度 0-1'),
        sa.Column('evidence', postgresql.JSONB(), nullable=True,
                  comment='支持归因的证据列表'),
        sa.Column('suggested_fix', sa.Text(), nullable=True,
                  comment='建议的修复方向'),
        sa.Column('attributed_by', sa.String(50), server_default='e8_auto',
                  comment='e8_auto/human'),
        sa.Column('attributed_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_eval_attr_result', 'eval_failure_attributions', ['result_id'])
    op.create_index('ix_eval_attr_layer', 'eval_failure_attributions', ['primary_layer'])
    op.create_index('ix_eval_attr_run', 'eval_failure_attributions', ['run_id'])


def downgrade() -> None:
    op.drop_index('ix_eval_attr_run', table_name='eval_failure_attributions')
    op.drop_index('ix_eval_attr_layer', table_name='eval_failure_attributions')
    op.drop_index('ix_eval_attr_result', table_name='eval_failure_attributions')
    op.drop_table('eval_failure_attributions')

    op.drop_index('ix_eval_results_run_case', table_name='eval_results')
    op.drop_index('ix_eval_results_verdict', table_name='eval_results')
    op.drop_index('ix_eval_results_case', table_name='eval_results')
    op.drop_index('ix_eval_results_run', table_name='eval_results')
    op.drop_table('eval_results')

    op.drop_index('ix_eval_runs_created', table_name='eval_runs')
    op.drop_index('ix_eval_runs_suite', table_name='eval_runs')
    op.drop_index('ix_eval_runs_status', table_name='eval_runs')
    op.drop_table('eval_runs')
