"""Update table and relation names

Revision ID: fb0582438012
Revises: da2ef53b641d
Create Date: 2021-05-13 14:51:39.611111

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fb0582438012'
down_revision = 'da2ef53b641d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('budget',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('category', sa.Enum('inc', 'exp', name='budgetcategoryenum'), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('examples', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('planned_amount', sa.Float(), nullable=False),
    sa.Column('month', sa.Date(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'month')
    )
    op.create_index(op.f('ix_budget_category'), 'budget', ['category'], unique=False)
    op.create_index(op.f('ix_budget_name'), 'budget', ['name'], unique=False)
    op.create_table('transaction',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('description', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('budget_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['budget_id'], ['budget.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_index('ix_budgets_category', table_name='budgets')
    op.drop_index('ix_budgets_name', table_name='budgets')
    op.drop_table('budgets')
    op.drop_table('transactions')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('password', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('is_admin', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='users_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_table('transactions',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('date', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('amount', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('budget_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], name='transactions_budget_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='transactions_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='transactions_pkey')
    )
    op.create_table('budgets',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('category', postgresql.ENUM('inc', 'exp', name='budgetcategoryenum'), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('examples', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    sa.Column('planned_amount', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('month', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='budgets_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='budgets_pkey'),
    sa.UniqueConstraint('name', 'month', name='budgets_name_month_key')
    )
    op.create_index('ix_budgets_name', 'budgets', ['name'], unique=False)
    op.create_index('ix_budgets_category', 'budgets', ['category'], unique=False)
    op.drop_table('transaction')
    op.drop_index(op.f('ix_budget_name'), table_name='budget')
    op.drop_index(op.f('ix_budget_category'), table_name='budget')
    op.drop_table('budget')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
