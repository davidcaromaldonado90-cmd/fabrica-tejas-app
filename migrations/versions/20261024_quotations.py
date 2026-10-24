"""Agrega cotizaciones y sus detalles comerciales.

Revision ID: 20261024_quotations
Revises: 20261023_password_reset_tokens
Create Date: 2026-10-24
"""

from alembic import op
import sqlalchemy as sa


revision = '20261024_quotations'
down_revision = '20261023_password_reset_tokens'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'cotizaciones' not in inspector.get_table_names():
        op.create_table(
            'cotizaciones',
            sa.Column('id_cotizacion', sa.Integer(), nullable=False),
            sa.Column('id_cliente', sa.Integer(), nullable=False),
            sa.Column('id_vendedor', sa.Integer(), nullable=True),
            sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
            sa.Column('vigencia_hasta', sa.Date(), nullable=False),
            sa.Column('estado', sa.Enum('Borrador', 'Enviada', 'Aceptada', 'Vencida', 'Convertida'), nullable=False),
            sa.Column('observacion', sa.String(length=300), nullable=True),
            sa.Column('total', sa.Numeric(12, 2), nullable=False),
            sa.Column('id_pedido', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['id_cliente'], ['clientes.id_cliente']),
            sa.ForeignKeyConstraint(['id_vendedor'], ['usuarios.id_usuario']),
            sa.ForeignKeyConstraint(['id_pedido'], ['pedidos.id_pedido']),
            sa.PrimaryKeyConstraint('id_cotizacion'),
            sa.UniqueConstraint('id_pedido', name='uq_cotizaciones_pedido'),
        )
    if 'detalle_cotizacion' not in inspector.get_table_names():
        op.create_table(
            'detalle_cotizacion',
            sa.Column('id_detalle_cotizacion', sa.Integer(), nullable=False),
            sa.Column('id_cotizacion', sa.Integer(), nullable=False),
            sa.Column('id_producto', sa.Integer(), nullable=False),
            sa.Column('color', sa.String(length=50), nullable=True),
            sa.Column('medida_metros', sa.Numeric(7, 2), nullable=False),
            sa.Column('cantidad', sa.Integer(), nullable=False),
            sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=False),
            sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
            sa.ForeignKeyConstraint(['id_cotizacion'], ['cotizaciones.id_cotizacion']),
            sa.ForeignKeyConstraint(['id_producto'], ['productos.id_producto']),
            sa.PrimaryKeyConstraint('id_detalle_cotizacion'),
        )


def downgrade():
    op.drop_table('detalle_cotizacion')
    op.drop_table('cotizaciones')