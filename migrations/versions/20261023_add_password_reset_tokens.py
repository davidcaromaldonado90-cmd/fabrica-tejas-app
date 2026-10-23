"""Agrega tokens de un solo uso para recuperación automática de contraseña.

Revision ID: 20261023_password_reset_tokens
Revises: 20260915_repair_cliente_usuario
Create Date: 2026-10-23
"""

from alembic import op
import sqlalchemy as sa


revision = '20261023_password_reset_tokens'
down_revision = '20260915_repair_cliente_usuario'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'tokens_recuperacion_contrasena' in inspector.get_table_names():
        return

    op.create_table(
        'tokens_recuperacion_contrasena',
        sa.Column('id_token', sa.Integer(), nullable=False),
        sa.Column('id_usuario', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.Column('fecha_expiracion', sa.DateTime(), nullable=False),
        sa.Column('usado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id_usuario']),
        sa.PrimaryKeyConstraint('id_token'),
        sa.UniqueConstraint('token_hash', name='uq_tokens_recuperacion_hash'),
    )
    op.create_index(
        'ix_tokens_recuperacion_usuario',
        'tokens_recuperacion_contrasena',
        ['id_usuario'],
        unique=False,
    )


def downgrade():
    op.drop_table('tokens_recuperacion_contrasena')