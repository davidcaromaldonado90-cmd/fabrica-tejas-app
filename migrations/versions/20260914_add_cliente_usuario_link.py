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
    op.add_column('clientes', sa.Column('id_usuario', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_clientes_id_usuario', 'clientes', 'usuarios', ['id_usuario'], ['id_usuario'])
    op.create_unique_constraint('uq_clientes_id_usuario', 'clientes', ['id_usuario'])


def downgrade():
    op.drop_constraint('uq_clientes_id_usuario', 'clientes', type_='unique')
    op.drop_constraint('fk_clientes_id_usuario', 'clientes', type_='foreignkey')
    op.drop_column('clientes', 'id_usuario')
