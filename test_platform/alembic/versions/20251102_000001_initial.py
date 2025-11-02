"""initial schema

Revision ID: 20251102_000001
Revises: 
Create Date: 2025-11-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251102_000001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'tests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('test_type', sa.String(length=10), nullable=False),
        sa.Column('access_key', sa.String(length=12), nullable=False),
        sa.Column('is_published', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_tests_title', 'tests', ['title'])
    op.create_index('ix_tests_access_key', 'tests', ['access_key'], unique=True)
    op.create_index('ix_tests_teacher_id', 'tests', ['teacher_id'])

    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_id', sa.Integer(), sa.ForeignKey('tests.id', ondelete='CASCADE')),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('correct_answer', sa.Integer(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('topic_tag', sa.String(length=120), nullable=True),
        sa.Column('difficulty', sa.String(length=10), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_questions_test_id', 'questions', ['test_id'])
    op.create_index('ix_questions_order', 'questions', ['order'])
    op.create_index('ix_questions_topic_tag', 'questions', ['topic_tag'])

    op.create_table(
        'attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_id', sa.Integer(), sa.ForeignKey('tests.id', ondelete='CASCADE')),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('time_taken', sa.Integer(), nullable=True),
        sa.Column('is_submitted', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_attempts_test_id', 'attempts', ['test_id'])
    op.create_index('ix_attempts_student_id', 'attempts', ['student_id'])


def downgrade() -> None:
    op.drop_table('attempts')
    op.drop_table('questions')
    op.drop_table('tests')
    op.drop_table('users')
