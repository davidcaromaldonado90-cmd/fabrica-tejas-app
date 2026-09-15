"""Vincula clientes con usuarios.

Revision ID: 20260914_cliente_usuario
Revises:
Create Date: 2026-09-14
"""

from alembic import op
import sqlalchemy as sa


revision = '20260914_cliente_usuario'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column['name'] for column in inspector.get_columns('clientes')}

    if 'id_usuario' not in columns:
        op.add_column('clientes', sa.Column('id_usuario', sa.Integer(), nullable=True))

    inspector = sa.inspect(bind)
    foreign_keys = {key.get('name') for key in inspector.get_foreign_keys('clientes')}
    if 'fk_clientes_id_usuario' not in foreign_keys:
        op.create_foreign_key('fk_clientes_id_usuario', 'clientes', 'usuarios', ['id_usuario'], ['id_usuario'])

    inspector = sa.inspect(bind)
    unique_constraints = {constraint.get('name') for constraint in inspector.get_unique_constraints('clientes')}
    if 'uq_clientes_id_usuario' not in unique_constraints:
        op.create_unique_constraint('uq_clientes_id_usuario', 'clientes', ['id_usuario'])


def downgrade():
    op.drop_constraint('uq_clientes_id_usuario', 'clientes', type_='unique')
    op.drop_constraint('fk_clientes_id_usuario', 'clientes', type_='foreignkey')
    op.drop_column('clientes', 'id_usuario')
