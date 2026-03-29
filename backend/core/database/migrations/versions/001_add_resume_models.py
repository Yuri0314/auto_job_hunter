"""add resume models

Revision ID: 001
Revises:
Create Date: 2026-03-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建 resumes 表
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), server_default='1'),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_type', sa.String(20), server_default='pdf'),
        sa.Column('parse_engine', sa.String(20), server_default='rule'),
        sa.Column('is_primary', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建 resume_profiles 表
    op.create_table(
        'resume_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50)),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('gender', sa.String(10)),
        sa.Column('age', sa.Integer()),
        sa.Column('experience_years', sa.Integer()),
        sa.Column('current_position', sa.String(100)),
        sa.Column('current_company', sa.String(200)),
        sa.Column('target_positions', sa.JSON()),
        sa.Column('preferred_cities', sa.JSON()),
        sa.Column('salary_min', sa.Integer()),
        sa.Column('salary_max', sa.Integer()),
        sa.Column('education', sa.String(50)),
        sa.Column('school', sa.String(100)),
        sa.Column('major', sa.String(100)),
        sa.Column('skills', sa.JSON()),
        sa.Column('work_experiences', sa.JSON()),
        sa.Column('projects', sa.JSON()),
        sa.Column('ai_search_suggestions', sa.JSON()),
        sa.Column('ai_match_summary', sa.Text()),
        sa.Column('raw_text', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建 search_strategies 表
    op.create_table(
        'search_strategies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('resume_id', sa.Integer()),
        sa.Column('primary_keywords', sa.JSON()),
        sa.Column('variant_keywords', sa.JSON()),
        sa.Column('skill_combinations', sa.JSON()),
        sa.Column('cities', sa.JSON()),
        sa.Column('salary_min', sa.Integer()),
        sa.Column('salary_max', sa.Integer()),
        sa.Column('exclude_keywords', sa.JSON()),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 为 jobs 表添加新字段
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.add_column(sa.Column('pool_status', sa.String(20), server_default='pending'))
        batch_op.add_column(sa.Column('starred_at', sa.DateTime()))
        batch_op.add_column(sa.Column('match_details', sa.JSON()))

    # 为 applications 表添加新字段
    with op.batch_alter_table('applications') as batch_op:
        batch_op.add_column(sa.Column('delivery_status', sa.String(20), server_default='submitted'))
        batch_op.add_column(sa.Column('status_updated_at', sa.DateTime()))
        batch_op.add_column(sa.Column('greeting_used', sa.Text()))

    # 为 user_profiles 表添加新字段
    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.add_column(sa.Column('run_mode', sa.String(20), server_default='manual'))
        batch_op.add_column(sa.Column('primary_resume_id', sa.Integer()))


def downgrade():
    op.drop_table('search_strategies')
    op.drop_table('resume_profiles')
    op.drop_table('resumes')

    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('pool_status')
        batch_op.drop_column('starred_at')
        batch_op.drop_column('match_details')

    with op.batch_alter_table('applications') as batch_op:
        batch_op.drop_column('delivery_status')
        batch_op.drop_column('status_updated_at')
        batch_op.drop_column('greeting_used')

    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.drop_column('run_mode')
        batch_op.drop_column('primary_resume_id')